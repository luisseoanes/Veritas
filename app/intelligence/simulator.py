"""Simulador contrafactual: "¿y si incorporo este producto, que recupero?".

Los detectores dicen QUE falta. Esto dice CUANTO VALE cerrarlo, y la cifra no
la estima nadie: se calcula RE-EJECUTANDO el solver real sobre las consultas
que de verdad se perdieron.

    1. Toma los eventos UNMET reales (conversaciones que no tuvieron solucion).
    2. Inserta un componente HIPOTETICO en una copia del grafo.
    3. Vuelve a resolver esos mismos requerimientos, uno por uno.
    4. Cuenta cuantos pasan de imposible a vendible, y cuanto dinero son.

Por que esto no es una proyeccion optimista: un perfil solo cuenta como
recuperado si el solver —el mismo que atiende a los clientes, con las mismas
reglas de ingenieria— encuentra una configuracion valida al anadir el producto.
Si el cliente chocaba con el presupuesto y no con el catalogo, sigue sin
solucion y se reporta aparte. El sistema no se miente a si mismo.

Esta capa NO toca el nucleo: construye un grafo aparte y lo descarta. El grafo
que atiende clientes nunca ve el producto hipotetico.
"""
from __future__ import annotations

from collections import defaultdict

from app.graph.schema import SOLUTION_SLOTS, Component, Kind
from app.graph.store import KnowledgeGraph
from app.intelligence.events import EventLog, EventType
from app.solver.engine import is_satisfiable
from app.solver.requirements import (
    AttributeRequirement,
    BudgetRequirement,
    FeatureRequirement,
    Requirement,
    StockRequirement,
)

# Mismo supuesto declarado que usan los detectores: se importa de alli para que
# no existan dos tasas de conversion distintas en el sistema.
from app.intelligence.detectors import ASSUMED_CONVERSION_RATE

# Factor de potencia tipico de un motor de induccion trifasico. Se usa solo para
# derivar la corriente del producto hipotetico cuando no se especifica.
POWER_FACTOR = 0.85


def _derive_current_a(power_kw: float, voltage: int, efficiency_pct: float) -> float:
    """I = P / (sqrt(3) * V * fp * eta). Misma formula documentada en catalog.py."""
    return round(
        (power_kw * 1000) / (1.732 * voltage * POWER_FACTOR * (efficiency_pct / 100)), 1
    )


def build_hypothetical(
    kind: Kind,
    power_kw: float,
    voltage: int,
    price_cop: int,
    features: list[str] | None = None,
    efficiency_pct: float = 91.0,
    margin_pct: float = 0.22,
    stock: int = 10,
) -> Component:
    """Producto que NO existe en el catalogo, para preguntarle al motor que pasaria."""
    attrs: dict = {
        "features": list(features or []),
        "tags": ["hipotetico"],
        "efficiency_pct": efficiency_pct,
    }
    if kind is Kind.MOTOR:
        attrs.update({
            "power_kw": power_kw,
            "voltage": voltage,
            "current_a": _derive_current_a(power_kw, voltage, efficiency_pct),
        })
    elif kind is Kind.DRIVE:
        attrs.update({
            "power_kw_max": power_kw,
            "current_a": _derive_current_a(power_kw, voltage, efficiency_pct) * 1.2,
            "voltage_min": int(voltage * 0.9),
            "voltage_max": int(voltage * 1.1),
        })
    else:
        attrs["current_a"] = _derive_current_a(power_kw, voltage, efficiency_pct)

    return Component(
        id=f"HIPOTETICO-{kind.value.upper()}-{power_kw:g}KW-{voltage}V",
        kind=kind,
        name=f"[HIPOTETICO] {kind.value} {power_kw:g} kW {voltage} V",
        price_cop=int(price_cop),
        margin_pct=margin_pct,
        stock=stock,
        attrs=attrs,
    )


def _graph_with(graph: KnowledgeGraph, extras: list[Component]) -> KnowledgeGraph:
    """Copia del grafo con componentes de mas. El original no se toca."""
    simulated = KnowledgeGraph()
    simulated.add_many(graph.all())
    simulated.add_many(extras)
    return simulated.build()


def diagnose_participation(graph: KnowledgeGraph, candidate: Component) -> dict | None:
    """¿Puede este producto formar alguna configuracion completa?

    Un producto puede tener compañeros compatibles en cada slot por separado y
    aun asi no servir para nada, porque dos de esos compañeros son incompatibles
    ENTRE SI. Caso real detectado con este simulador: un motor de 22 kW a 220 V
    admite variadores (desde 130 A) y protecciones (hasta 125 A), pero ninguna
    proteccion del catalogo cubre la corriente de entrada de esos variadores.
    Resultado: el motor es invendible aunque parezca compatible con todo.

    Sin este diagnostico el simulador devolveria un cero mudo. Devuelve None si
    el producto SI participa en alguna configuracion valida.
    """
    others = [k for k in SOLUTION_SLOTS if k is not candidate.kind and graph.of_kind(k)]
    # `pair_allowed` y NO `compatible_with`: cuando ninguna regla gobierna un par
    # (proteccion y cable, por ejemplo) no hay arista, pero tampoco prohibicion.
    # Usar las aristas daria por invendible a un producto perfectamente valido.
    options = {
        k: [c for c in graph.of_kind(k) if graph.pair_allowed(candidate.id, c.id)]
        for k in others
    }

    vacios = [k.value for k, v in options.items() if not v]
    if vacios:
        return {
            "utilizable": False,
            "motivo": "SIN_COMPATIBLES",
            "slots_sin_opcion": vacios,
            "explicacion": (
                f"No existe ningun {', '.join(vacios)} en el catalogo compatible con "
                f"este producto. Anadirlo no habilita ninguna venta."
            ),
        }

    # Los compañeros existen; ¿son compatibles entre si?
    for i, k1 in enumerate(others):
        for k2 in others[i + 1:]:
            if any(
                graph.pair_allowed(a.id, b.id)
                for a in options[k1] for b in options[k2]
            ):
                continue
            peor = min(options[k1], key=lambda c: c.attrs.get("current_a", 0))
            mejor = max(options[k2], key=lambda c: c.attrs.get("current_a", 0))
            return {
                "utilizable": False,
                "motivo": "COMPAÑEROS_INCOMPATIBLES",
                "slots_en_conflicto": [k1.value, k2.value],
                "explicacion": (
                    f"El producto admite {k1.value} y {k2.value} por separado, pero "
                    f"ninguna pareja de ambos es compatible entre si. El {k1.value} "
                    f"mas pequeno que le sirve exige {peor.attrs.get('current_a')} A y "
                    f"el {k2.value} mas grande del catalogo llega a "
                    f"{mejor.attrs.get('current_a')} A."
                ),
                "para_cerrar_la_brecha": (
                    f"No basta con anadir este producto: hace falta ademas un "
                    f"{k2.value} de al menos {peor.attrs.get('current_a')} A."
                ),
            }
    return None


def _requirements_from_event(req: dict) -> list[Requirement]:
    """Reconstruye las restricciones de una consulta perdida.

    Se rearman aqui en vez de reutilizar las de `app.agent` para que esta capa
    no dependa del agente: la inteligencia de negocio se apoya en el solver,
    nunca al reves.
    """
    out: list[Requirement] = []
    if req.get("power_kw") is not None:
        out.append(AttributeRequirement(Kind.MOTOR, "power_kw", ">=", req["power_kw"]))
    if req.get("voltage") is not None:
        out.append(AttributeRequirement(Kind.MOTOR, "voltage", "==", req["voltage"]))
    for feature in req.get("features") or []:
        out.append(FeatureRequirement(feature))
    if req.get("require_stock", True):
        out.append(StockRequirement(1))
    if req.get("budget_cop") is not None:
        out.append(BudgetRequirement(int(req["budget_cop"])))
    return out


def _profile_key(req: dict) -> tuple:
    """Perfiles identicos se resuelven UNA vez y se multiplican por su frecuencia.

    De ~130 consultas perdidas suelen salir unas pocas decenas de perfiles
    distintos: es lo que mantiene la simulacion por debajo del segundo.
    """
    return (
        req.get("power_kw"),
        req.get("voltage"),
        req.get("budget_cop"),
        tuple(sorted(req.get("features") or [])),
        bool(req.get("require_stock", True)),
    )


def simulate(
    events: EventLog,
    graph: KnowledgeGraph,
    candidates: Component | list[Component],
) -> dict:
    """Que recuperaria el negocio si incorporara estos productos al catalogo.

    Acepta uno o varios: cerrar una brecha suele exigir mas de una referencia
    (un motor nuevo puede necesitar tambien la proteccion que lo acompane), y
    evaluarlos por separado daria cero en ambos casos.
    """
    if isinstance(candidates, Component):
        candidates = [candidates]
    unmet = events.of_type(EventType.UNMET)
    if not unmet:
        return {
            "status": "SIN_HISTORICO",
            "nota": (
                "No hay consultas sin solucion registradas todavia. Genera "
                "historico (scripts/generate_history.py) o espera conversaciones "
                "reales: sin fracasos no hay nada que recuperar."
            ),
        }

    simulated_graph = _graph_with(graph, candidates)

    # Antes de contar dinero: ¿son siquiera vendibles estos productos? Un cero
    # sin explicacion es inutil para decidir.
    diagnosticos = [
        {"producto": c.id, **d}
        for c in candidates
        if (d := diagnose_participation(simulated_graph, c)) is not None
    ]

    grouped: dict[tuple, list] = defaultdict(list)
    for event in unmet:
        grouped[_profile_key(event.requirements)].append(event)

    recovered, still_blocked = [], []
    for key, group in grouped.items():
        requirements = _requirements_from_event(group[0].requirements)
        if not requirements:
            continue

        power_kw, voltage, budget_cop, features, _ = key
        budgets = [
            e.requirements.get("budget_cop") for e in group
            if e.requirements.get("budget_cop")
        ]
        avg_budget = int(sum(budgets) / len(budgets)) if budgets else None

        entry = {
            "clientes": len(group),
            "perfil": {
                "power_kw": power_kw, "voltage": voltage,
                "features": list(features), "presupuesto_cop": budget_cop,
            },
            "presupuesto_promedio_cop": avg_budget,
        }

        if is_satisfiable(simulated_graph, requirements):
            entry["valor_recuperable_cop"] = int(
                len(group) * (avg_budget or 0) * ASSUMED_CONVERSION_RATE
            )
            recovered.append(entry)
        else:
            # Honestidad: por que este sigue perdido pese al producto nuevo.
            entry["sigue_bloqueado_por"] = sorted(
                {c for e in group for c in e.unsat_core}
            )
            still_blocked.append(entry)

    total_clientes = len(unmet)
    recuperados = sum(e["clientes"] for e in recovered)
    valor = sum(e.get("valor_recuperable_cop", 0) for e in recovered)

    return {
        "status": "OK",
        "productos_simulados": [
            {
                "id": c.id,
                "tipo": c.kind.value,
                "precio_cop": c.price_cop,
                "atributos": {k: v for k, v in c.attrs.items() if k != "tags"},
            }
            for c in candidates
        ],
        # Presente solo si algun producto NO puede formar configuracion valida.
        # Es lo que convierte un "0 recuperados" en una recomendacion accionable.
        "diagnostico_de_viabilidad": diagnosticos or None,
        "consultas_perdidas_analizadas": total_clientes,
        "perfiles_distintos": len(grouped),
        "clientes_recuperados": recuperados,
        "clientes_que_siguen_sin_solucion": total_clientes - recuperados,
        "tasa_de_recuperacion": (
            round(recuperados / total_clientes, 3) if total_clientes else 0.0
        ),
        "valor_recuperable_cop": valor,
        "formula": (
            f"{recuperados} clientes recuperados x presupuesto promedio de su perfil "
            f"x {ASSUMED_CONVERSION_RATE:.0%} de conversion asumida = ${valor:,}"
        ),
        "metodo": (
            "Cada perfil se volvio a resolver con el MISMO solver y las MISMAS "
            "reglas de ingenieria, sobre un grafo que incluye el producto "
            "hipotetico. Un perfil cuenta como recuperado solo si existe una "
            "configuracion tecnicamente valida. Ninguna cifra la estima el modelo."
        ),
        "detalle_recuperados": sorted(
            recovered, key=lambda e: e.get("valor_recuperable_cop", 0), reverse=True
        )[:10],
        "detalle_no_recuperados": sorted(
            still_blocked, key=lambda e: e["clientes"], reverse=True
        )[:5],
    }
