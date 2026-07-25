"""Herramientas del chatbot administrador (BI conversacional).

CERO logica nueva: cada tool envuelve codigo que YA existe y que los endpoints
`/admin/*` ya exponen. El chatbot admin es el mismo motor visto en lenguaje
natural — no un segundo cerebro. Ver docs/03 §5.

Dos invariantes que NO se relajan:
  1. NINGUNA de estas tools registra eventos. Las de lectura solo leen; la unica
     de escritura (`set_business_objective`) cambia una POLITICA, no el log de
     mercado. Asi el chatbot admin no contamina la evidencia de negocio que
     miden los detectores (solo cuentan conversaciones reales de clientes). Esto
     sale gratis por no darle `solve_configuration` al perfil admin.
  2. El LLM sigue sin decidir numeros: cada cifra viene de un detector (con su
     formula), del grafo o del solver.
"""
from __future__ import annotations

from app.agent.registry import registry
from app.agent.tools import _build_requirements
from app.graph.queries import sole_option_bottlenecks
from app.intelligence.detectors import detect_all
from app.intelligence.events import EventType, event_log
from app.solver.engine import solve
from app.solver.pareto import (
    BUSINESS_OBJECTIVES,
    frontier_payload,
    pareto_frontier,
    select_on_frontier,
)
from app.state import state


@registry.tool(
    name="get_opportunities",
    description=(
        "Inteligencia de negocio en vivo: oportunidades detectadas sobre las "
        "conversaciones reales de clientes (demanda insatisfecha, brechas de "
        "catalogo, brechas de precio, productos que faltan y para cuantos "
        "clientes). Cada deteccion trae su FORMULA visible. Usala para preguntas "
        "como '¿que producto me falta y para cuantos clientes?'."
    ),
    parameters={"type": "object", "properties": {}, "required": []},
)
def get_opportunities() -> dict:
    """Envuelve `detect_all` (intelligence/detectors.py). Solo lee el event_log."""
    report = detect_all(event_log, state.graph)
    report["resumen"] = {
        "conversaciones_totales": len(event_log),
        "resueltas": len(event_log.of_type(EventType.SOLVED)),
        "sin_solucion": len(event_log.of_type(EventType.UNMET)),
        "objetivo_activo": state.objective_key,
    }
    return report


@registry.tool(
    name="get_bottlenecks",
    description=(
        "Cuellos de botella ESTRUCTURALES del catalogo: componentes que son la "
        "unica opcion compatible para algun perfil, es decir, puntos donde el "
        "catalogo no tiene alternativa. Analitica del grafo, independiente de las "
        "conversaciones. Usala para '¿que restriccion bloquea mas ventas?'."
    ),
    parameters={"type": "object", "properties": {}, "required": []},
)
def get_bottlenecks() -> dict:
    """Envuelve `sole_option_bottlenecks` (graph/queries.py)."""
    return {"cuellos_de_botella": sole_option_bottlenecks(state.graph)}


@registry.tool(
    name="get_frontier",
    description=(
        "La frontera de Pareto de un escenario concreto: dado un conjunto de "
        "requerimientos (los mismos que /solve), devuelve la frontera, las "
        "soluciones dominadas y que punto elegiria CADA objetivo de negocio. "
        "Usala para 'muestrame la frontera para 5 kW a 440 V'. Los numeros salen "
        "del solver, no del modelo."
    ),
    parameters={
        "type": "object",
        "properties": {
            "power_kw": {"type": "number", "description": "Potencia minima requerida en kW"},
            "voltage": {"type": "integer", "description": "Voltaje de la red disponible (220 o 440)"},
            "budget_cop": {"type": "integer", "description": "Presupuesto maximo total en pesos colombianos"},
            "features": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Caracteristicas exigidas: soft_start, modbus, profibus, pid, ip66",
            },
            "require_stock": {
                "type": "boolean",
                "description": "Exigir disponibilidad inmediata en inventario (por defecto true)",
            },
        },
        "required": [],
    },
)
def get_frontier(
    power_kw: float | None = None,
    voltage: int | None = None,
    budget_cop: int | None = None,
    features: list[str] | None = None,
    require_stock: bool = True,
) -> dict:
    """Envuelve `solve` + `pareto_frontier` (igual que POST /admin/frontier).

    NO registra eventos: `solve` es puro; el registro vive solo en la tool
    `solve_configuration`, que este perfil no tiene.
    """
    requirements = _build_requirements(power_kw, voltage, budget_cop, features, require_stock)
    if not requirements:
        return {"status": "SIN_REQUERIMIENTOS",
                "mensaje": "Da al menos un requerimiento (potencia, voltaje, presupuesto...)."}

    result = solve(state.graph, requirements)
    if not result.satisfiable:
        return {
            "status": "SIN_SOLUCION",
            "nucleo_insatisfacible": [r.name for r in result.unsat_core],
        }

    frontier = pareto_frontier(result.solutions)
    frontier_ids = {tuple(c.ids) for c in frontier}
    dominated = [c for c in result.solutions if tuple(c.ids) not in frontier_ids]

    chosen_by_objective = {}
    for key, objective in BUSINESS_OBJECTIVES.items():
        chosen, _ranking = select_on_frontier(frontier, objective)
        chosen_by_objective[key] = {
            "ids": list(chosen.ids),
            "precio_cop": chosen.total_price_cop,
        }

    return {
        "status": "OK",
        "frontera": frontier_payload(frontier),
        "dominadas": frontier_payload(dominated),
        "elegida_por_objetivo": chosen_by_objective,
    }


@registry.tool(
    name="get_active_objective",
    description=(
        "El objetivo de negocio activo ahora mismo y los presets disponibles. "
        "El objetivo decide que punto DENTRO de la frontera se recomienda; nunca "
        "saca al cliente de la frontera. Consultala antes de proponer un cambio."
    ),
    parameters={"type": "object", "properties": {}, "required": []},
)
def get_active_objective() -> dict:
    """Envuelve `state.objective` / `BUSINESS_OBJECTIVES` (igual que /admin/objectives)."""
    return {
        "activo": state.objective_key,
        "disponibles": [
            {"clave": key, "etiqueta": obj.label, "pesos": obj.weights}
            for key, obj in BUSINESS_OBJECTIVES.items()
        ],
        "garantia": (
            "Los objetivos solo eligen un punto DENTRO de la frontera de Pareto. "
            "Ninguna configuracion dominada es alcanzable, sea cual sea el objetivo."
        ),
    }


@registry.tool(
    name="set_business_objective",
    description=(
        "UNICA accion con efecto del chatbot admin: cambia el objetivo de negocio "
        "activo. Solo acepta uno de los 4 presets validos (balanced, "
        "customer_value, maximize_margin, clear_inventory); cualquier otro valor "
        "se rechaza. CAMBIO GLOBAL: afecta de inmediato lo que el asesor "
        "recomienda a los clientes. CONFIRMA con el administrador antes de "
        "aplicarlo; nunca lo cambies ante una pregunta hipotetica."
    ),
    parameters={
        "type": "object",
        "properties": {
            "key": {
                "type": "string",
                "enum": list(BUSINESS_OBJECTIVES),
                "description": "El preset a activar.",
            },
        },
        "required": ["key"],
    },
)
def set_business_objective(key: str) -> dict:
    """Envuelve `state.set_objective` (state.py) — ESCRITURA.

    `state.set_objective` valida contra los 4 presets y lanza ValueError con un
    valor desconocido: el modelo no puede inventar una politica. No registra
    eventos (cambia una politica, no el log de mercado).
    """
    objective = state.set_objective(key)  # ValueError si el preset no existe
    return {
        "status": "OBJETIVO_CAMBIADO",
        "activo": state.objective_key,
        "etiqueta": objective.label,
        "pesos": objective.weights,
        "efecto": "Afecta de inmediato lo que el asesor recomienda a los clientes.",
    }
