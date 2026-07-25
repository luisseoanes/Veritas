"""Requerimientos del cliente, modelados como restricciones nombradas.

Cada requerimiento es un objeto identificable y RETIRABLE. Esa propiedad es lo
que hace posible el nucleo insatisfacible: cuando no hay solucion, el solver
puede decir *cual* de estos rompio el problema, en vez de un "no encontre nada".

Las reglas tecnicas de compatibilidad (app/graph/rules.py) NO viven aqui: son
la teoria de fondo, no son negociables y por tanto nunca forman parte del
nucleo. El nucleo siempre esta compuesto por lo que el cliente pidio.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.graph.schema import Component, Configuration, Kind

Op = Literal[">=", "<=", "=="]


class Requirement:
    """Restriccion nombrada sobre una configuracion.

    `prefilter` permite podar candidatos slot por slot antes de combinar
    (optimizacion). `satisfied_by` es la verdad: decide sobre la configuracion
    completa.
    """

    name: str
    description: str

    def prefilter(self, component: Component) -> bool:
        """False descarta el componente antes de combinar. Por defecto no poda."""
        return True

    def satisfied_by(self, config: Configuration) -> bool:
        raise NotImplementedError

    def to_dict(self) -> dict:
        return {"name": self.name, "description": self.description}

    def __repr__(self) -> str:
        return f"<{self.name}>"


@dataclass(init=False)
class AttributeRequirement(Requirement):
    """Restringe un atributo tecnico de un tipo de componente.

    Ej: el motor debe entregar al menos 15 kW  ->
        AttributeRequirement(Kind.MOTOR, "power_kw", ">=", 15)
    """

    kind: Kind
    attribute: str
    op: Op
    value: float

    def __init__(self, kind: Kind, attribute: str, op: Op, value: float, label: str | None = None):
        self.kind = kind
        self.attribute = attribute
        self.op = op
        self.value = value
        self.name = f"{kind.value}.{attribute}{op}{value:g}"
        self.description = label or f"El {kind.value} debe cumplir {attribute} {op} {value:g}"

    def _compare(self, actual: float) -> bool:
        if self.op == ">=":
            return actual >= self.value
        if self.op == "<=":
            return actual <= self.value
        return actual == self.value

    def prefilter(self, component: Component) -> bool:
        if component.kind is not self.kind:
            return True
        actual = component.attrs.get(self.attribute)
        return actual is not None and self._compare(actual)

    def satisfied_by(self, config: Configuration) -> bool:
        component = config.components.get(self.kind)
        if component is None:
            return False
        actual = component.attrs.get(self.attribute)
        return actual is not None and self._compare(actual)


@dataclass(init=False)
class BudgetRequirement(Requirement):
    """Restriccion global: el precio total de la solucion no puede excederse.

    Es global (depende de todos los slots), asi que no poda nada por adelantado.
    En la practica es la restriccion que mas aparece en los nucleos
    insatisfacibles — y la mas valiosa comercialmente.
    """

    max_cop: int

    def __init__(self, max_cop: int):
        self.max_cop = max_cop
        self.name = f"budget<={max_cop}"
        self.description = f"El costo total no puede exceder ${max_cop:,} COP"

    def satisfied_by(self, config: Configuration) -> bool:
        return config.total_price_cop <= self.max_cop


@dataclass(init=False)
class FeatureRequirement(Requirement):
    """Exige que algun componente de la solucion aporte una caracteristica.

    Ej: arranque suave, comunicacion Modbus, grado IP66.
    """

    feature: str

    def __init__(self, feature: str, label: str | None = None):
        self.feature = feature
        self.name = f"feature:{feature}"
        self.description = label or f"La solucion debe incluir '{feature}'"

    def satisfied_by(self, config: Configuration) -> bool:
        return any(self.feature in c.features for c in config.components.values())


@dataclass(init=False)
class StockRequirement(Requirement):
    """Exige disponibilidad inmediata de todos los componentes."""

    min_units: int

    def __init__(self, min_units: int = 1):
        self.min_units = min_units
        self.name = f"stock>={min_units}"
        self.description = f"Todos los componentes deben tener al menos {min_units} unidad(es) en stock"

    def prefilter(self, component: Component) -> bool:
        return component.stock >= self.min_units

    def satisfied_by(self, config: Configuration) -> bool:
        return config.min_stock >= self.min_units
