"""Modelo de dominio del grafo de conocimiento.

El catalogo NO se modela como una lista de productos, sino como una red de
componentes con atributos tecnicos. Las aristas de compatibilidad no se
escriben a mano: se DERIVAN de reglas de ingenieria (ver
`app/graph/store.py::build_graph`). Esa derivacion es, literalmente, la
construccion del grafo.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum


class Kind(str, Enum):
    """Tipo de componente. Un nodo del grafo es siempre uno de estos."""

    MOTOR = "motor"
    DRIVE = "drive"            # Variador de frecuencia (VFD)
    PROTECTION = "protection"  # Contactor / guardamotor
    CABLE = "cable"


@dataclass(frozen=True)
class Component:
    """Nodo del grafo. Un producto real con sus atributos tecnicos y comerciales.

    `attrs` guarda los atributos especificos del tipo (potencia, corriente,
    rango de voltaje...). Se mantiene generico a proposito: si el dia del reto
    cambia el dominio, solo cambian los atributos y las reglas — no el motor.
    """

    id: str
    kind: Kind
    name: str
    price_cop: int          # Precio en pesos colombianos
    margin_pct: float       # Margen bruto (0.0 - 1.0)
    stock: int              # Unidades en inventario
    attrs: dict = field(default_factory=dict)

    # --- Accesos tipados a atributos comunes (evita strings magicos regados) ---

    @property
    def power_kw(self) -> float | None:
        return self.attrs.get("power_kw")

    @property
    def current_a(self) -> float | None:
        return self.attrs.get("current_a")

    @property
    def features(self) -> set[str]:
        return set(self.attrs.get("features", []))

    def accepts_voltage(self, volts: int) -> bool:
        """True si el componente opera al voltaje dado.

        Motores declaran `voltage` puntual; variadores un rango
        [voltage_min, voltage_max]; el resto es agnostico al voltaje.
        """
        if "voltage" in self.attrs:
            return int(self.attrs["voltage"]) == volts
        lo, hi = self.attrs.get("voltage_min"), self.attrs.get("voltage_max")
        if lo is not None and hi is not None:
            return lo <= volts <= hi
        return True

    @property
    def margin_cop(self) -> int:
        return int(self.price_cop * self.margin_pct)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["kind"] = self.kind.value
        return d

    def __str__(self) -> str:
        return f"{self.id} ({self.name})"


# Orden canonico en que se arma una solucion. El solver recorre los tipos en
# este orden, y el cliente ve la configuracion presentada asi.
SOLUTION_SLOTS: tuple[Kind, ...] = (
    Kind.MOTOR,
    Kind.DRIVE,
    Kind.PROTECTION,
    Kind.CABLE,
)


@dataclass(frozen=True)
class Configuration:
    """Una solucion candidata: un componente por cada slot.

    Es el objeto que el solver produce, Pareto filtra y el agente explica.
    """

    components: dict[Kind, Component]

    @property
    def total_price_cop(self) -> int:
        return sum(c.price_cop for c in self.components.values())

    @property
    def total_margin_cop(self) -> int:
        return sum(c.margin_cop for c in self.components.values())

    @property
    def min_stock(self) -> int:
        """Disponibilidad real de la configuracion = la del componente mas escaso."""
        return min(c.stock for c in self.components.values())

    def get(self, kind: Kind) -> Component:
        return self.components[kind]

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(self.components[k].id for k in SOLUTION_SLOTS if k in self.components)

    def to_dict(self) -> dict:
        return {
            "components": {k.value: c.to_dict() for k, c in self.components.items()},
            "total_price_cop": self.total_price_cop,
            "total_margin_cop": self.total_margin_cop,
            "min_stock": self.min_stock,
        }

    def __str__(self) -> str:
        parts = " + ".join(self.components[k].id for k in SOLUTION_SLOTS if k in self.components)
        return f"[{parts}] ${self.total_price_cop:,}"
