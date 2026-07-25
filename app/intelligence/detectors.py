"""Motor de deteccion de oportunidades.

Regla de integridad de este modulo: **los numeros los calcula el codigo, el LLM
solo los interpreta.** Cada oportunidad viaja con su campo `formula`, que
expone la derivacion completa y los supuestos. Un numero sin formula visible es
un numero inventado; aqui no se produce ninguno.

Tres detectores:
  1. Demanda no satisfecha  — de los fracasos del solver (nucleos insatisfacibles)
  2. Brecha de bundle       — co-ocurrencia en soluciones recomendadas
  3. Riesgo de inventario   — cuello de botella del grafo x demanda real
"""
from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations

from app.graph.queries import sole_option_bottlenecks
from app.graph.store import KnowledgeGraph
from app.intelligence.events import EventLog, EventType

# --- Supuestos declarados. Se muestran en la UI junto a cada cifra. ----------
# No son datos: son premisas de un modelo. Se exponen para que la estimacion
# sea auditable en vez de una cifra salida de la nada.
ASSUMED_CONVERSION_RATE = 0.15   # Fraccion de consultas que se vuelven venta
MIN_COOCCURRENCE_FOR_BUNDLE = 3  # Umbral para proponer un bundle


def unmet_demand(events: EventLog, top_n: int = 5) -> list[dict]:
    """Demanda que el catalogo no pudo atender, agrupada por causa raiz.

    Agrupa los eventos UNMET por su nucleo insatisfacible + el perfil tecnico
    pedido. El resultado no es "no encontramos nada": es "N clientes chocaron
    con LA MISMA restriccion, y esto es lo que faltaria para atenderlos".
    """
    buckets: dict[tuple, list] = defaultdict(list)

    for event in events.of_type(EventType.UNMET):
        req = event.requirements
        key = (
            tuple(sorted(event.unsat_core)),
            req.get("power_kw"),
            req.get("voltage"),
        )
        buckets[key].append(event)

    opportunities = []
    for (core, power_kw, voltage), group in buckets.items():
        viables = [e.minimum_viable_cop for e in group if e.minimum_viable_cop]
        budgets = [e.requirements.get("budget_cop") for e in group if e.requirements.get("budget_cop")]

        min_viable = min(viables) if viables else None
        avg_budget = int(sum(budgets) / len(budgets)) if budgets else None
        addressable = int(len(group) * (avg_budget or min_viable or 0) * ASSUMED_CONVERSION_RATE)

        # Dos naturalezas muy distintas de oportunidad, y el nucleo las separa
        # solo: si el presupuesto NO aparece en el, el problema no es el precio
        # — es que el catalogo no cubre ese perfil tecnico a ningun precio.
        # Esa es la senal mas accionable que produce el sistema.
        is_price_gap = any(c.startswith("budget") for c in core)

        if is_price_gap and power_kw and voltage and avg_budget and min_viable:
            gap = min_viable - avg_budget
            recomendacion = (
                f"BRECHA DE PRECIO: existe solucion tecnica para {power_kw:g} kW a "
                f"{voltage} V, pero cuesta ${min_viable:,} y estos clientes traen "
                f"${avg_budget:,} en promedio. Faltan ${gap:,} de cobertura. "
                f"Evaluar una linea de entrada para este rango."
            )
        elif not is_price_gap and power_kw and voltage:
            recomendacion = (
                f"BRECHA DE PRODUCTO: el catalogo no cubre {power_kw:g} kW a "
                f"{voltage} V a NINGUN precio — estos clientes tienen "
                f"${avg_budget:,} en promedio y no hay nada que venderles. "
                f"Evaluar incorporar referencia para este perfil."
                if avg_budget else
                f"BRECHA DE PRODUCTO: el catalogo no cubre {power_kw:g} kW a {voltage} V."
            )
        else:
            recomendacion = f"Revisar cobertura de catalogo para el nucleo {list(core)}."

        opportunities.append({
            "tipo": "demanda_no_satisfecha",
            "naturaleza": "brecha_de_precio" if is_price_gap else "brecha_de_producto",
            "clientes_afectados": len(group),
            "restriccion_causante": list(core),
            "perfil": {"power_kw": power_kw, "voltage": voltage},
            "presupuesto_promedio_cop": avg_budget,
            "minimo_viable_cop": min_viable,
            "brecha_cop": (min_viable - avg_budget) if (min_viable and avg_budget) else None,
            "demanda_direccionable_cop": addressable,
            "formula": (
                f"{len(group)} clientes x ${avg_budget or 0:,} presupuesto promedio "
                f"x {ASSUMED_CONVERSION_RATE:.0%} conversion asumida = ${addressable:,}"
            ),
            "recomendacion": recomendacion,
        })

    return sorted(opportunities, key=lambda o: o["demanda_direccionable_cop"], reverse=True)[:top_n]


def bundle_gaps(
    events: EventLog,
    graph: KnowledgeGraph,
    top_n: int = 5,
) -> list[dict]:
    """Pares de componentes que se recomiendan juntos pero se venden sueltos.

    Co-ocurrencia sobre las configuraciones efectivamente recomendadas. Si dos
    componentes aparecen sistematicamente en la misma solucion, existe un SKU
    de bundle que el negocio no esta ofreciendo.
    """
    pair_counts: Counter = Counter()

    for event in events.of_type(EventType.SOLVED):
        for a, b in combinations(sorted(event.configuration), 2):
            pair_counts[(a, b)] += 1

    gaps = []
    for (a_id, b_id), count in pair_counts.items():
        if count < MIN_COOCCURRENCE_FOR_BUNDLE:
            continue
        a, b = graph.get(a_id), graph.get(b_id)
        combined_margin = a.margin_cop + b.margin_cop
        impact = int(count * combined_margin * ASSUMED_CONVERSION_RATE)

        gaps.append({
            "tipo": "brecha_de_bundle",
            "componentes": [a_id, b_id],
            "nombres": [a.name, b.name],
            "co_ocurrencias": count,
            "margen_combinado_cop": combined_margin,
            "impacto_estimado_cop": impact,
            "formula": (
                f"{count} co-ocurrencias x ${combined_margin:,} margen combinado "
                f"x {ASSUMED_CONVERSION_RATE:.0%} conversion asumida = ${impact:,}"
            ),
            "recomendacion": f"Crear bundle '{a.name} + {b.name}' con descuento de paquete.",
        })

    return sorted(gaps, key=lambda g: g["impacto_estimado_cop"], reverse=True)[:top_n]


def inventory_risk(
    events: EventLog,
    graph: KnowledgeGraph,
    top_n: int = 5,
) -> list[dict]:
    """Cuellos de botella de compatibilidad ponderados por demanda real.

    Este detector es el que una base vectorial no puede replicar: cruza la
    ESTRUCTURA del grafo (que componente es la unica opcion compatible para
    otros) con la DEMANDA observada (cuantas veces entro en una recomendacion).
    Un componente con stock bajo, unico en su rol y muy demandado es el riesgo
    de inventario mas caro que tiene la empresa.
    """
    demand: Counter = Counter()
    for event in events.of_type(EventType.SOLVED):
        demand.update(event.configuration)

    risks = []
    for bottleneck in sole_option_bottlenecks(graph):
        cid = bottleneck["component_id"]
        component = graph.get(cid)
        times_recommended = demand.get(cid, 0)
        dependents = bottleneck["sole_option_for"]
        stock = component.stock

        # Riesgo alto = muy demandado, insustituible y con poco inventario.
        risk_score = round((times_recommended + dependents) / max(stock, 1), 2)
        exposure = int(times_recommended * component.price_cop * ASSUMED_CONVERSION_RATE)

        risks.append({
            "tipo": "riesgo_de_inventario",
            "componente": cid,
            "nombre": component.name,
            "stock": stock,
            "unica_opcion_para": dependents,
            "veces_recomendado": times_recommended,
            "indice_riesgo": risk_score,
            "exposicion_cop": exposure,
            "formula": (
                f"({times_recommended} recomendaciones + {dependents} dependientes) "
                f"/ {stock} unidades en stock = indice {risk_score}"
            ),
            "recomendacion": (
                f"Si {cid} se agota, {dependents} componente(s) del catalogo quedan "
                f"sin alternativa compatible. Priorizar reposicion."
            ),
        })

    return sorted(risks, key=lambda r: r["indice_riesgo"], reverse=True)[:top_n]


def detect_all(events: EventLog, graph: KnowledgeGraph) -> dict:
    """Corre los tres detectores. Es lo que consume el dashboard."""
    return {
        "supuestos": {
            "tasa_conversion_asumida": ASSUMED_CONVERSION_RATE,
            "umbral_co_ocurrencia_bundle": MIN_COOCCURRENCE_FOR_BUNDLE,
            "nota": (
                "Los impactos economicos son estimaciones bajo estos supuestos "
                "declarados, calculadas por codigo sobre datos reales de las "
                "conversaciones. Ninguna cifra proviene del modelo de lenguaje."
            ),
        },
        "demanda_no_satisfecha": unmet_demand(events),
        "brechas_de_bundle": bundle_gaps(events, graph),
        "riesgo_de_inventario": inventory_risk(events, graph),
        "eventos_analizados": len(events),
    }
