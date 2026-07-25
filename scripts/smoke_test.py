"""Verificacion de punta a punta del motor. Corre SIN API key.

Prueba lo que hay que defender ante el jurado:
  1. El grafo deriva sus aristas de reglas, no de datos escritos a mano.
  2. El solver encuentra configuraciones validas y sabe justificarlas.
  3. La frontera de Pareto no contiene soluciones dominadas.
  4. Los objetivos de negocio cambian la eleccion PERO nunca salen de la frontera.
  5. Cuando no hay solucion, el nucleo insatisfacible es minimal y correcto.
  6. La capa RAG prepara y respalda, pero NUNCA decide una configuracion.

Uso:  python -m scripts.smoke_test
"""
from __future__ import annotations

import sys

from app.data.catalog import load_graph
from app.graph.queries import betweenness_bottlenecks, sole_option_bottlenecks
from app.graph.schema import Kind
from app.solver.engine import explain, solve
from app.solver.pareto import (
    BUSINESS_OBJECTIVES,
    dominates,
    OBJECTIVES,
    pareto_frontier,
    select_on_frontier,
)
from app.solver.requirements import (
    AttributeRequirement,
    BudgetRequirement,
    FeatureRequirement,
    StockRequirement,
)

failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    mark = "OK  " if condition else "FALLA"
    print(f"  [{mark}] {label}" + (f" -> {detail}" if detail else ""))
    if not condition:
        failures.append(label)


def section(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


def money(v: float) -> str:
    return f"${v:,.0f}"


# ---------------------------------------------------------------------------
section("1. GRAFO DE CONOCIMIENTO")

graph = load_graph()
stats = graph.stats()
print(f"  Componentes: {stats['components']}  |  Aristas derivadas: {stats['edges']}")
print(f"  Por tipo: {stats['by_kind']}")
print(f"  Reglas de compatibilidad activas: {stats['rules']}")

check("El grafo tiene componentes", stats["components"] > 0)
check("Las aristas se derivaron de reglas", stats["edges"] > 0, f"{stats['edges']} aristas")

motor_15_220 = graph.get("MOT-W22-15-220")
drives_ok = graph.compatible_with(motor_15_220.id, Kind.DRIVE)
print(f"\n  Variadores compatibles con {motor_15_220.id}: {[d.id for d in drives_ok]}")
check("Un motor de 15kW/220V tiene variador compatible", len(drives_ok) > 0)
check(
    "Ningun variador de 440V aparece como compatible con un motor de 220V",
    all(d.accepts_voltage(220) for d in drives_ok),
)

ev = graph.evidence("MOT-W22-15-220", "DRV-CFW300-4-220")
check(
    "Un variador subdimensionado es rechazado con evidencia",
    ev["compatible"] is False and any(not r["passes"] for r in ev["rules_evaluated"]),
    next(r["name"] for r in ev["rules_evaluated"] if not r["passes"]),
)

# ---------------------------------------------------------------------------
section("2. SOLVER — CASO SATISFACIBLE")

sat_reqs = [
    AttributeRequirement(Kind.MOTOR, "power_kw", ">=", 5.5, "Necesita al menos 5.5 kW"),
    AttributeRequirement(Kind.MOTOR, "voltage", "==", 220, "Red disponible: 220V"),
    FeatureRequirement("soft_start", "Requiere arranque suave"),
    StockRequirement(1),
    BudgetRequirement(8_000_000),
]

result = solve(graph, sat_reqs)
print(f"  Configuraciones evaluadas: {result.considered}")
print(f"  Soluciones validas: {result.count}")

check("Encuentra solucion", result.satisfiable and result.count > 0)

if result.satisfiable:
    cheapest = min(result.solutions, key=lambda c: c.total_price_cop)
    print(f"  Mas economica: {cheapest}")

    check(
        "Toda solucion respeta el presupuesto",
        all(c.total_price_cop <= 8_000_000 for c in result.solutions),
    )
    check(
        "Toda solucion cumple la potencia minima",
        all(c.get(Kind.MOTOR).attrs["power_kw"] >= 5.5 for c in result.solutions),
    )
    check(
        "Toda solucion opera a 220V",
        all(c.get(Kind.MOTOR).attrs["voltage"] == 220 for c in result.solutions),
    )

    evidence = explain(graph, cheapest)
    print(f"  Pares verificados en la evidencia: {len(evidence['checks'])}")
    check("La evidencia de la solucion pasa todas las reglas", evidence["all_rules_pass"])

# ---------------------------------------------------------------------------
section("3. FRONTERA DE PARETO")

frontier = pareto_frontier(result.solutions)
print(f"  Soluciones factibles: {len(result.solutions)}  ->  Frontera: {len(frontier)}")

check("La frontera no esta vacia", len(frontier) > 0)
check("La frontera es subconjunto de las factibles", len(frontier) <= len(result.solutions))
check(
    "Ninguna solucion de la frontera esta dominada",
    not any(
        dominates(other, f, OBJECTIVES)
        for f in frontier
        for other in result.solutions
        if other is not f
    ),
)

# ---------------------------------------------------------------------------
section("4. OBJETIVOS DE NEGOCIO SOBRE LA FRONTERA")

frontier_ids = {f.ids for f in frontier}
elecciones = {}

for key, objective in BUSINESS_OBJECTIVES.items():
    chosen, ranking = select_on_frontier(frontier, objective)
    elecciones[key] = chosen.ids
    print(
        f"  {objective.label:<32} -> {money(chosen.total_price_cop):>14}"
        f" | margen {money(chosen.total_margin_cop):>12} | stock {chosen.min_stock:>2}"
    )
    check(
        f"'{objective.label}' elige DENTRO de la frontera",
        chosen.ids in frontier_ids,
    )

check(
    "Objetivos distintos producen elecciones distintas",
    len(set(elecciones.values())) > 1,
    f"{len(set(elecciones.values()))} configuraciones distintas entre {len(elecciones)} objetivos",
)

margen = BUSINESS_OBJECTIVES["maximize_margin"]
valor = BUSINESS_OBJECTIVES["customer_value"]
c_margen, _ = select_on_frontier(frontier, margen)
c_valor, _ = select_on_frontier(frontier, valor)
check(
    "'Maximizar margen' no elige una solucion mas barata que 'mejor valor'",
    c_margen.total_margin_cop >= c_valor.total_margin_cop,
    f"margen {money(c_margen.total_margin_cop)} vs {money(c_valor.total_margin_cop)}",
)

# ---------------------------------------------------------------------------
section("5. NUCLEO INSATISFACIBLE — EL DIAGNOSTICO CAUSAL")

unsat_reqs = [
    AttributeRequirement(Kind.MOTOR, "power_kw", ">=", 15, "Necesita al menos 15 kW"),
    AttributeRequirement(Kind.MOTOR, "voltage", "==", 220, "Red disponible: 220V"),
    FeatureRequirement("soft_start", "Requiere arranque suave"),
    StockRequirement(1),
    BudgetRequirement(3_500_000),
]

unsat = solve(graph, unsat_reqs)
check("El problema es correctamente insatisfacible", not unsat.satisfiable)

print(f"\n  Requerimientos del cliente: {len(unsat_reqs)}")
print(f"  Nucleo minimo insatisfacible: {len(unsat.unsat_core)}")
for req in unsat.unsat_core:
    print(f"    - {req.name}: {req.description}")

check(
    "El nucleo es mas pequeno que el conjunto completo",
    0 < len(unsat.unsat_core) < len(unsat_reqs),
)

# Minimalidad: quitar cualquier elemento del nucleo debe volverlo satisfacible.
from app.solver.engine import _is_satisfiable  # noqa: E402

minimal = all(
    _is_satisfiable(graph, [r for r in unsat.unsat_core if r is not dropped])
    for dropped in unsat.unsat_core
)
check("El nucleo es MINIMAL (quitar cualquier elemento lo vuelve satisfacible)", minimal)

print("\n  Relajaciones — que pasa si el cliente cede en cada restriccion:")
for rel in unsat.relaxations:
    line = f"    - Ceder '{rel['requirement']}' habilita {rel['solutions_unlocked']} soluciones"
    if "minimum_viable_cop" in rel:
        line += (
            f"\n        minimo viable: {money(rel['minimum_viable_cop'])}"
            f"  (faltan {money(rel['gap_cop'])})"
            f"\n        configuracion: {' + '.join(rel['cheapest_configuration'])}"
        )
    print(line)

budget_rel = next((r for r in unsat.relaxations if "minimum_viable_cop" in r), None)
check("Reporta el minimo viable cuando el presupuesto es la causa", budget_rel is not None)
if budget_rel:
    check("El minimo viable excede el presupuesto pedido", budget_rel["gap_cop"] > 0)

# ---------------------------------------------------------------------------
section("6. CUELLOS DE BOTELLA — ANALITICA NATIVA DEL GRAFO")

sole = sole_option_bottlenecks(graph)
print("  Componentes que son UNICA opcion compatible para otros:")
for entry in sole[:5]:
    print(
        f"    - {entry['component_id']:<20} ({entry['kind']:<10}) "
        f"unica opcion de {entry['sole_option_for']:>2} componentes | stock {entry['stock']}"
    )
check("Detecta al menos un cuello de botella estructural", len(sole) > 0)

between = betweenness_bottlenecks(graph, top_n=3)
print("\n  Mayor centralidad de intermediacion:")
for entry in between:
    print(f"    - {entry['component_id']:<20} betweenness={entry['betweenness']}")
check("Calcula centralidad sobre el grafo", len(between) > 0)

# ---------------------------------------------------------------------------
section("7. CAPA RAG — PREPARA Y RESPALDA, PERO NO DECIDE")

# El indice de la prueba vive aparte del real y siempre en modo mock: esta
# verificacion tiene que correr sin API key, igual que el resto del smoke test.
import json  # noqa: E402
import shutil  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

from app.config import settings  # noqa: E402

_smoke_chroma = Path(tempfile.gettempdir()) / "reshapex_smoke_chroma"
shutil.rmtree(_smoke_chroma, ignore_errors=True)
settings.embedding_provider = "mock"
settings.chroma_path = str(_smoke_chroma)

from app.agent.tools import cite_datasheet, suggest_requirements  # noqa: E402
from app.retrieval import profiles as profile_corpus  # noqa: E402
from app.state import state as app_state  # noqa: E402

retrieval = app_state.retrieval
print(f"  Embedder: {retrieval.embedder.name} ({retrieval.embedder.dim} dims)")
print(f"  Umbrales: perfiles {retrieval.profiles.min_score} | "
      f"hojas de datos {retrieval.datasheets.min_score}")

check(
    "El indice de perfiles se construye",
    retrieval.profiles.count() == len(profile_corpus.PROFILES),
    f"{retrieval.profiles.count()} perfiles indexados",
)

# Un perfil que sugiere una caracteristica inexistente condena al cliente a un
# insatisfacible causado por el propio sistema.
huerfanas = profile_corpus.unknown_features(graph)
check(
    "Ningun perfil sugiere una caracteristica ausente del catalogo",
    not huerfanas,
    f"huerfanas: {huerfanas}" if huerfanas else "todas existen",
)

# --- Recuperacion: la descripcion del cliente llega a los perfiles correctos ---
consulta = (
    "necesito mover cajas en una banda transportadora que se lava con manguera "
    "a presion todos los dias"
)
sugerencia = json.loads(suggest_requirements(consulta))
print(f"\n  Cliente: \"{consulta}\"")
print(f"  Estado: {sugerencia['status']}")
for s in sugerencia.get("sugerencias", []):
    print(f"    - {s['perfil']:<24} {s['restricciones']}  (conf. {s['confianza']})")

check(
    "Devuelve sugerencias SIN CONFIRMAR, no decisiones",
    sugerencia["status"] == "SUGERENCIAS_SIN_CONFIRMAR",
)

combinado = sugerencia.get("combinado_si_el_cliente_confirma_todo", {})
features_sugeridas = set(combinado.get("features", []))
print(f"  Combinado: {combinado}")

check(
    "Reconoce la banda transportadora -> soft_start",
    "soft_start" in features_sugeridas,
)
check(
    "Reconoce el lavado a presion -> ip66",
    "ip66" in features_sugeridas,
)
check(
    "Toda sugerencia viaja con su justificacion",
    all(s.get("porque") for s in sugerencia["sugerencias"]),
)
check(
    "Declara que potencia y voltaje no se infieren",
    len(sugerencia.get("faltante_obligatorio", [])) == 2,
)

# --- LA VERIFICACION QUE IMPORTA: el RAG no puede colar un producto ---
texto_crudo = json.dumps(sugerencia, ensure_ascii=False)
ids_del_catalogo = [c.id for c in graph.all()]
check(
    "NINGUN id de producto aparece en la respuesta del RAG",
    not any(cid in texto_crudo for cid in ids_del_catalogo),
    "el RAG propone restricciones, nunca componentes",
)
check(
    "La respuesta del RAG no contiene precios",
    "precio" not in texto_crudo and "_cop" not in texto_crudo,
)

# --- Umbral: fuera de dominio no se responde con lo mas parecido ---
# Se verifica el UMBRAL, no la calidad semantica: en modo mock la similitud es
# lexica, asi que una consulta fuera de dominio que comparta una raiz con el
# corpus ("cuanto CUESTA" vs "CUESTA arrancar") si recuperaria algo. Esa
# confusion desaparece con el embedder de Gemini, que es el de la demo.
fuera = json.loads(suggest_requirements(
    "quiero reservar una mesa en un restaurante para ocho personas el sabado"
))
print(f"\n  Consulta fuera de dominio -> {fuera['status']}")
check(
    "Una consulta fuera de dominio no recupera nada",
    fuera["status"] == "SIN_COINCIDENCIAS",
    "el umbral filtra en vez de devolver lo menos malo",
)

# --- Conflicto: no se inventa un desempate ---
ambigua = json.loads(suggest_requirements(
    "se quemo el motor y la linea esta parada, pero tambien estamos cotizando "
    "para un proyecto del proximo ano sin afan"
))
print(f"  Consulta contradictoria -> conflictos: {len(ambigua.get('conflictos', []))}")
check(
    "Detecta urgencia y no-urgencia como conflicto en vez de elegir una",
    len(ambigua.get("conflictos", [])) > 0
    and "require_stock" not in ambigua.get("combinado_si_el_cliente_confirma_todo", {}),
)

# --- El puente cierra: lo sugerido pasa por el solver como cualquier otra cosa ---
reqs_desde_rag = [
    # Potencia y voltaje los da el cliente, nunca el RAG.
    AttributeRequirement(Kind.MOTOR, "power_kw", ">=", 7.5, "Cliente: 7.5 kW"),
    AttributeRequirement(Kind.MOTOR, "voltage", "==", 440, "Cliente: red de 440V"),
    *[FeatureRequirement(f) for f in sorted(features_sugeridas)],
    StockRequirement(1),
]
resultado_rag = solve(graph, reqs_desde_rag)
print(f"\n  Restricciones confirmadas -> solver: {len(reqs_desde_rag)} restricciones, "
      f"{resultado_rag.count} soluciones")

check(
    "Las restricciones sugeridas por el RAG las resuelve el solver",
    resultado_rag.satisfiable and resultado_rag.count > 0,
)
if resultado_rag.satisfiable:
    check(
        "Toda solucion cumple de verdad las caracteristicas sugeridas",
        all(
            all(any(f in c.features for c in config.components.values())
                for f in features_sugeridas)
            for config in resultado_rag.solutions
        ),
        f"features verificadas: {sorted(features_sugeridas)}",
    )

# --- Degradacion honesta: sin corpus indexado, no se inventan citas ---
cita = json.loads(cite_datasheet("cada cuanto se lubrican los rodamientos"))
print(f"\n  cite_datasheet sin hojas de datos indexadas -> {cita['status']}")
check(
    "Sin corpus, cite_datasheet lo declara en vez de inventar",
    cita["status"] == "SIN_CORPUS" and "fragmentos" not in cita,
)

# --- Troceo: las tablas no entran al indice, la prosa que las rodea si ---
from app.retrieval.chunks import Chunk, _prose_blocks  # noqa: E402

pagina_cruda = (
    "Tabla de seleccion\n"
    "1 4.2 CFW500A04P2S2 $ 1,240\n"
    "2 7.0 CFW500A07P0S2 $ 1,680\n"
    "Mantenimiento preventivo. Los condensadores del bus DC deben reformarse\n"
    "si el equipo permanece almacenado sin energizar por mas de dos anos.\n"
)
bloques = _prose_blocks(pagina_cruda)
print(f"\n  Troceo de una pagina con tabla -> {len(bloques)} bloques de prosa")
check(
    "Las filas de tabla no llegan al indice vectorial",
    not any("1,240" in b or "CFW500A04P2S2" in b for b in bloques),
    "los precios se leen del grafo, nunca de un texto recuperado",
)
check(
    "La prosa que rodea a la tabla si se conserva",
    any("condensadores" in b for b in bloques),
)

# --- Citacion: el fragmento indexado se recupera con documento y pagina ---
retrieval.datasheets.add([Chunk(
    text=(
        "Condiciones ambientales de operacion. El variador opera entre -10 C y "
        "+50 C sin reduccion de capacidad. La instalacion por encima de 1000 "
        "metros sobre el nivel del mar exige una reduccion adicional del 1% de "
        "corriente por cada 100 metros de altitud."
    ),
    source="manual-de-prueba.pdf",
    page=7,
    component_ids=["DRV-CFW500-11-440"],
)])

cita = json.loads(cite_datasheet("puedo instalarlo a 2500 metros de altitud?"))
print(f"  cite_datasheet con corpus -> {cita['status']}")
check(
    "Recupera el fragmento pertinente con su fuente",
    cita["status"] == "CON_RESPALDO"
    and cita["fragmentos"][0]["documento"] == "manual-de-prueba.pdf"
    and cita["fragmentos"][0]["pagina"] == 7,
    "documento y pagina citables",
)

ajena = json.loads(cite_datasheet("cual es el horario de atencion en Bogota"))
check(
    "Una pregunta ajena al corpus no recupera el fragmento mas parecido",
    ajena["status"] == "SIN_RESPALDO",
)

shutil.rmtree(_smoke_chroma, ignore_errors=True)

# ---------------------------------------------------------------------------
section("RESULTADO")

if failures:
    print(f"  {len(failures)} verificacion(es) fallaron:")
    for f in failures:
        print(f"    - {f}")
    sys.exit(1)

print("  Todas las verificaciones pasaron. El motor esta sano.")
