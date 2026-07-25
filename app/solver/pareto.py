"""Frontera de Pareto y seleccion por objetivos de negocio.

Esta es la respuesta tecnica a la pregunta incomoda: *"si el negocio dirige las
recomendaciones, no estan manipulando al cliente?"*

No. Porque los objetivos de negocio no eligen entre TODAS las soluciones: solo
eligen un punto **sobre la frontera de Pareto**. Una solucion dominada — peor o
igual en todos los criterios que otra disponible — es matematicamente
inalcanzable, sin importar como se configuren los objetivos.

El negocio decide el punto. La frontera decide el conjunto. El cliente nunca
sale de ella.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from app.graph.schema import Configuration, Kind

Direction = Literal["min", "max"]


@dataclass(frozen=True)
class Objective:
    """Criterio de evaluacion de una configuracion."""

    name: str
    extract: Callable[[Configuration], float]
    direction: Direction
    label: str

    def value(self, config: Configuration) -> float:
        return float(self.extract(config))

    def normalized(self, config: Configuration, lo: float, hi: float) -> float:
        """Escala a [0,1] donde 1 siempre es 'mejor', sin importar la direccion."""
        if hi == lo:
            return 1.0
        raw = (self.value(config) - lo) / (hi - lo)
        return raw if self.direction == "max" else 1.0 - raw


def _motor_efficiency(config: Configuration) -> float:
    motor = config.components.get(Kind.MOTOR)
    return motor.attrs.get("efficiency_pct", 0.0) if motor else 0.0


OBJECTIVES: tuple[Objective, ...] = (
    Objective("cost", lambda c: c.total_price_cop, "min", "Costo total"),
    Objective("margin", lambda c: c.total_margin_cop, "max", "Margen bruto"),
    Objective("availability", lambda c: c.min_stock, "max", "Disponibilidad"),
    Objective("efficiency", _motor_efficiency, "max", "Eficiencia del motor"),
)

OBJECTIVES_BY_NAME = {o.name: o for o in OBJECTIVES}


# ----------------------------------------------------------------- dominancia


def dominates(a: Configuration, b: Configuration, objectives: tuple[Objective, ...]) -> bool:
    """`a` domina a `b`: no es peor en ningun objetivo y es mejor en al menos uno."""
    at_least_as_good = True
    strictly_better = False

    for obj in objectives:
        va, vb = obj.value(a), obj.value(b)
        if obj.direction == "min":
            va, vb = -va, -vb  # Normaliza todo a "mas es mejor".
        if va < vb:
            at_least_as_good = False
            break
        if va > vb:
            strictly_better = True

    return at_least_as_good and strictly_better


def _dominates_vector(a: tuple[float, ...], b: tuple[float, ...]) -> bool:
    """Igual que `dominates`, pero sobre vectores ya normalizados a 'mas es mejor'."""
    strictly_better = False
    for va, vb in zip(a, b):
        if va < vb:
            return False
        if va > vb:
            strictly_better = True
    return strictly_better


def pareto_frontier(
    solutions: list[Configuration],
    objectives: tuple[Objective, ...] = OBJECTIVES,
) -> list[Configuration]:
    """Filtra las soluciones no dominadas.

    Sigue siendo O(n^2) comparaciones, pero los valores de cada objetivo se
    calculan UNA vez por solucion en vez de una vez por comparacion. Importa:
    `total_price_cop` y `total_margin_cop` recorren los componentes en cada
    acceso, asi que la version ingenua los recalculaba millones de veces. Con
    ~1500 soluciones factibles eso costaba ~4.5 s dentro de una respuesta de
    chat; precalcular lo baja a decimas.

    El signo se invierte aqui para los objetivos de minimizar, de modo que la
    comparacion interna sea siempre "mas es mejor".
    """
    signs = tuple(-1.0 if obj.direction == "min" else 1.0 for obj in objectives)
    vectors = [
        tuple(sign * obj.value(c) for obj, sign in zip(objectives, signs))
        for c in solutions
    ]

    frontier = []
    for i, candidate in enumerate(vectors):
        if not any(j != i and _dominates_vector(other, candidate)
                   for j, other in enumerate(vectors)):
            frontier.append(solutions[i])
    return frontier


# ------------------------------------------------------- objetivos de negocio


@dataclass
class BusinessObjective:
    """Politica comercial del administrador.

    `weights` pondera los objetivos al elegir sobre la frontera. `boost_tags`
    favorece componentes de familias concretas (impulsar una linea). Ninguno de
    los dos puede sacar la seleccion de la frontera de Pareto.
    """

    key: str
    label: str
    weights: dict[str, float]
    boost_tags: tuple[str, ...] = ()
    boost_strength: float = 0.25

    def score(self, config: Configuration, bounds: dict[str, tuple[float, float]]) -> float:
        total = 0.0
        for name, weight in self.weights.items():
            obj = OBJECTIVES_BY_NAME[name]
            lo, hi = bounds[name]
            total += weight * obj.normalized(config, lo, hi)

        if self.boost_tags:
            tags = {t for c in config.components.values() for t in c.attrs.get("tags", [])}
            if tags & set(self.boost_tags):
                total += self.boost_strength

        return total


# Presets. El administrador los activa desde el panel; el agente no los conoce
# como texto libre, solo como politica estructurada.
BUSINESS_OBJECTIVES: dict[str, BusinessObjective] = {
    "balanced": BusinessObjective(
        key="balanced",
        label="Equilibrado (por defecto)",
        weights={"cost": 0.4, "efficiency": 0.3, "availability": 0.2, "margin": 0.1},
    ),
    "customer_value": BusinessObjective(
        key="customer_value",
        label="Mejor valor para el cliente",
        weights={"cost": 0.6, "efficiency": 0.4},
    ),
    "maximize_margin": BusinessObjective(
        key="maximize_margin",
        label="Maximizar margen",
        weights={"margin": 0.7, "cost": 0.15, "efficiency": 0.15},
    ),
    "clear_inventory": BusinessObjective(
        key="clear_inventory",
        label="Liberar inventario",
        weights={"availability": 0.65, "cost": 0.25, "efficiency": 0.10},
    ),
}


def bounds_over(
    solutions: list[Configuration],
    objectives: tuple[Objective, ...] = OBJECTIVES,
) -> dict[str, tuple[float, float]]:
    """Rango [min, max] de cada objetivo, para normalizar la puntuacion."""
    return {
        obj.name: (
            min(obj.value(s) for s in solutions),
            max(obj.value(s) for s in solutions),
        )
        for obj in objectives
    }


def select_on_frontier(
    frontier: list[Configuration],
    objective: BusinessObjective,
) -> tuple[Configuration, list[dict]]:
    """Elige un punto de la frontera segun la politica del negocio.

    Devuelve (elegida, ranking completo). El ranking se expone en el dashboard
    para que sea auditable que la eleccion ocurrio DENTRO de la frontera.
    """
    if not frontier:
        raise ValueError("La frontera de Pareto esta vacia")

    bounds = bounds_over(frontier)
    scored = sorted(
        (
            {
                "configuration": c,
                "ids": c.ids,
                "score": round(objective.score(c, bounds), 4),
                "objectives": {o.name: o.value(c) for o in OBJECTIVES},
            }
            for c in frontier
        ),
        key=lambda e: e["score"],
        reverse=True,
    )
    return scored[0]["configuration"], scored


def frontier_payload(frontier: list[Configuration]) -> list[dict]:
    """Serializa la frontera para graficarla en el dashboard."""
    return [
        {
            "ids": c.ids,
            "objectives": {o.name: o.value(c) for o in OBJECTIVES},
            "total_price_cop": c.total_price_cop,
            "total_margin_cop": c.total_margin_cop,
            "min_stock": c.min_stock,
        }
        for c in frontier
    ]
