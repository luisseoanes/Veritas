"""Solver simbolico de configuracion.

Este modulo es la garantia del sistema. El LLM NUNCA elige una configuracion:
traduce la necesidad del cliente a requerimientos, y este solver decide. Si el
solver no lo aprueba, no se recomienda. Por construccion, es imposible que el
agente proponga una configuracion tecnicamente invalida.

Cuando NO hay solucion, el solver no se rinde: extrae el **nucleo minimo
insatisfacible** (MUS) — el subconjunto mas pequeno de requerimientos del
cliente que ya es imposible por si solo. Ese nucleo es el diagnostico causal
que alimenta la inteligencia de negocio.

Algoritmo del MUS: eliminacion (deletion-based MUS). Se intenta retirar cada
requerimiento uno por uno; si el problema sigue siendo insatisfacible sin el,
ese requerimiento era prescindible y se descarta. Lo que queda es minimal: no
se le puede quitar nada sin volverlo satisfacible.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

from app.graph.rules import rules_for
from app.graph.schema import Component, Configuration, Kind, SOLUTION_SLOTS
from app.graph.store import KnowledgeGraph
from app.solver.requirements import BudgetRequirement, Requirement

# Tope de soluciones enumeradas. El espacio real de configuraciones de producto
# es pequeno; este limite solo protege contra un catalogo mal cargado.
MAX_SOLUTIONS = 2000


@dataclass
class SolveResult:
    """Resultado del solver. `satisfiable` decide como leerlo."""

    satisfiable: bool
    solutions: list[Configuration] = field(default_factory=list)
    unsat_core: list[Requirement] = field(default_factory=list)
    relaxations: list[dict] = field(default_factory=list)
    considered: int = 0

    @property
    def count(self) -> int:
        return len(self.solutions)

    def to_dict(self) -> dict:
        return {
            "satisfiable": self.satisfiable,
            "solution_count": self.count,
            "solutions": [s.to_dict() for s in self.solutions],
            "unsat_core": [r.to_dict() for r in self.unsat_core],
            "relaxations": self.relaxations,
            "configurations_considered": self.considered,
        }


# --------------------------------------------------------------- enumeracion


def _candidates(graph: KnowledgeGraph, kind: Kind, requirements: list[Requirement]) -> list[Component]:
    """Componentes de un slot que sobreviven a los prefiltros unarios."""
    return [c for c in graph.of_kind(kind) if all(r.prefilter(c) for r in requirements)]


def _enumerate(
    graph: KnowledgeGraph,
    requirements: list[Requirement],
    stop_at_first: bool = False,
) -> tuple[list[Configuration], int]:
    """Enumera configuraciones validas por backtracking sobre los slots.

    Poda temprano: un componente solo se agrega si es compatible con TODOS los
    ya elegidos, segun el grafo. Eso evita construir combinaciones condenadas.

    Devuelve (soluciones, configuraciones_completas_evaluadas).
    """
    slots = [k for k in SOLUTION_SLOTS if graph.of_kind(k)]
    pools = {k: _candidates(graph, k, requirements) for k in slots}

    # Si algun slot quedo vacio tras los prefiltros, no hay solucion posible.
    if any(not pools[k] for k in slots):
        return [], 0

    solutions: list[Configuration] = []
    considered = 0

    def backtrack(index: int, chosen: dict[Kind, Component]) -> bool:
        """Devuelve True para abortar la busqueda (corte temprano)."""
        nonlocal considered

        if index == len(slots):
            considered += 1
            config = Configuration(components=dict(chosen))
            if all(r.satisfied_by(config) for r in requirements):
                solutions.append(config)
                if stop_at_first or len(solutions) >= MAX_SOLUTIONS:
                    return True
            return False

        kind = slots[index]
        for candidate in pools[kind]:
            if not all(graph.pair_allowed(candidate.id, c.id) for c in chosen.values()):
                continue
            chosen[kind] = candidate
            if backtrack(index + 1, chosen):
                del chosen[kind]
                return True
            del chosen[kind]
        return False

    backtrack(0, {})
    return solutions, considered


def _is_satisfiable(graph: KnowledgeGraph, requirements: list[Requirement]) -> bool:
    """Existe al menos una configuracion valida. Corta en la primera."""
    solutions, _ = _enumerate(graph, requirements, stop_at_first=True)
    return bool(solutions)


# ----------------------------------------------- nucleo minimo insatisfacible


def find_unsat_core(graph: KnowledgeGraph, requirements: list[Requirement]) -> list[Requirement]:
    """Extrae un nucleo minimo insatisfacible por eliminacion.

    Precondicion: `requirements` en conjunto es insatisfacible.

    Invariante del bucle: `core` siempre es insatisfacible. Al retirar un
    requerimiento, si el resto SIGUE siendo insatisfacible, ese requerimiento
    no era responsable y se descarta. Al terminar, todo elemento restante es
    necesario para la contradiccion — eso es la minimalidad.
    """
    core = list(requirements)
    for candidate in list(core):
        reduced = [r for r in core if r is not candidate]
        if not reduced:
            continue
        if not _is_satisfiable(graph, reduced):
            core = reduced
    return core


def _explain_relaxations(
    graph: KnowledgeGraph,
    core: list[Requirement],
    all_requirements: list[Requirement],
) -> list[dict]:
    """Que pasaria si el cliente cediera en cada requerimiento del nucleo.

    Esto convierte "no hay solucion" en una negociacion concreta. Para el
    presupuesto ademas calcula el minimo viable real: el precio de la
    configuracion mas barata que cumple todo lo demas.

    Cada relajacion viaja con una PROPUESTA concreta: la configuracion mas
    barata que existiria si el cliente cediera en ese punto, con sus ids y su
    precio. Sin eso, "podrias ceder en X" es una abstraccion que el cliente no
    puede aceptar; con eso es una oferta sobre la mesa. Se elige la mas barata
    a proposito: es un criterio neutral y auditable, no una politica comercial
    (los objetivos de negocio viven en otra capa y no pueden entrar aqui).
    """
    relaxations = []
    for req in core:
        without = [r for r in all_requirements if r is not req]
        solutions, _ = _enumerate(graph, without)
        entry = {
            "requirement": req.name,
            "description": req.description,
            "solutions_unlocked": len(solutions),
        }
        if solutions:
            cheapest = min(solutions, key=lambda c: c.total_price_cop)
            entry["proposal"] = {
                "configuration": list(cheapest.ids),
                "total_price_cop": cheapest.total_price_cop,
                "min_stock": cheapest.min_stock,
                "components": {
                    kind.value: {"id": c.id, "name": c.name, "price_cop": c.price_cop}
                    for kind, c in cheapest.components.items()
                },
            }
            if isinstance(req, BudgetRequirement):
                entry["minimum_viable_cop"] = cheapest.total_price_cop
                entry["gap_cop"] = cheapest.total_price_cop - req.max_cop
                entry["cheapest_configuration"] = cheapest.ids
        relaxations.append(entry)
    return sorted(relaxations, key=lambda e: e["solutions_unlocked"], reverse=True)


# ------------------------------------------------------------------ API publica


def solve(graph: KnowledgeGraph, requirements: list[Requirement]) -> SolveResult:
    """Resuelve la configuracion. Unica puerta de entrada del sistema.

    SAT   -> devuelve todas las configuraciones tecnicamente validas.
    UNSAT -> devuelve el nucleo minimo insatisfacible y las relajaciones.
    """
    requirements = list(requirements)
    solutions, considered = _enumerate(graph, requirements)

    if solutions:
        return SolveResult(satisfiable=True, solutions=solutions, considered=considered)

    core = find_unsat_core(graph, requirements)
    return SolveResult(
        satisfiable=False,
        unsat_core=core,
        relaxations=_explain_relaxations(graph, core, requirements),
        considered=considered,
    )


def explain(graph: KnowledgeGraph, config: Configuration) -> dict:
    """Rastro de evidencia de una configuracion.

    Devuelve cada par de componentes con las reglas que lo gobiernan y su
    resultado. Es el "camino del grafo" que se muestra en la demo para probar
    que la recomendacion esta fundamentada y no generada por el modelo.
    """
    checks = []
    for a, b in combinations(config.components.values(), 2):
        applicable = rules_for(a, b)
        if not applicable:
            continue
        checks.append({
            "pair": [a.id, b.id],
            "rules": [
                {"name": r.name, "description": r.description, "passes": r.holds(a, b)}
                for r in applicable
            ],
        })
    return {
        "configuration": config.ids,
        "total_price_cop": config.total_price_cop,
        "checks": checks,
        "all_rules_pass": all(rc["passes"] for c in checks for rc in c["rules"]),
    }
