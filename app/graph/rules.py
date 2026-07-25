"""Reglas de compatibilidad tecnica entre componentes.

Estas reglas son la fuente de verdad del grafo: las aristas `COMPATIBLE_WITH`
se derivan aplicandolas a cada par de componentes. Estan basadas en practica
estandar de dimensionamiento de circuitos de motor (factor 1.25 sobre corriente
nominal para proteccion y conductor, holgura de 1.1 en el variador).

Cambiar el dominio el dia del reto = reescribir este archivo. Nada mas.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.graph.schema import Component, Kind

# Factores de dimensionamiento (documentados, no numeros magicos)
PROTECTION_SIZING_FACTOR = 1.25  # Proteccion >= 125% de la corriente del motor
CABLE_SIZING_FACTOR = 1.25       # Conductor  >= 125% de la corriente del motor
DRIVE_HEADROOM_FACTOR = 1.10     # Variador   >= 110% de la corriente del motor


@dataclass(frozen=True)
class CompatibilityRule:
    """Regla que decide si dos componentes de tipos distintos pueden convivir."""

    name: str
    kind_a: Kind
    kind_b: Kind
    predicate: Callable[[Component, Component], bool]
    description: str

    def holds(self, a: Component, b: Component) -> bool:
        """Evalua la regla respetando el orden (kind_a, kind_b)."""
        if a.kind is self.kind_a and b.kind is self.kind_b:
            return self.predicate(a, b)
        if b.kind is self.kind_a and a.kind is self.kind_b:
            return self.predicate(b, a)
        return True  # La regla no aplica a este par: no lo restringe.

    def applies_to(self, a: Component, b: Component) -> bool:
        return {a.kind, b.kind} == {self.kind_a, self.kind_b}


def _drive_supports_motor(drive: Component, motor: Component) -> bool:
    """El variador debe cubrir potencia, voltaje y corriente del motor."""
    if drive.attrs["power_kw_max"] < motor.attrs["power_kw"]:
        return False
    if not drive.accepts_voltage(motor.attrs["voltage"]):
        return False
    return drive.attrs["current_a"] >= motor.attrs["current_a"] * DRIVE_HEADROOM_FACTOR


def _protection_covers_motor(protection: Component, motor: Component) -> bool:
    return protection.attrs["current_a"] >= motor.attrs["current_a"] * PROTECTION_SIZING_FACTOR


def _cable_carries_motor(cable: Component, motor: Component) -> bool:
    return cable.attrs["ampacity_a"] >= motor.attrs["current_a"] * CABLE_SIZING_FACTOR


def _protection_covers_drive(protection: Component, drive: Component) -> bool:
    """La proteccion aguas arriba debe soportar la corriente de entrada del variador."""
    return protection.attrs["current_a"] >= drive.attrs["current_a"]


COMPATIBILITY_RULES: tuple[CompatibilityRule, ...] = (
    CompatibilityRule(
        name="drive_supports_motor",
        kind_a=Kind.DRIVE,
        kind_b=Kind.MOTOR,
        predicate=_drive_supports_motor,
        description=(
            f"El variador debe cubrir la potencia del motor, aceptar su voltaje y "
            f"entregar al menos {DRIVE_HEADROOM_FACTOR:.0%} de su corriente nominal."
        ),
    ),
    CompatibilityRule(
        name="protection_covers_motor",
        kind_a=Kind.PROTECTION,
        kind_b=Kind.MOTOR,
        predicate=_protection_covers_motor,
        description=(
            f"La proteccion debe dimensionarse a >= {PROTECTION_SIZING_FACTOR:.0%} "
            f"de la corriente nominal del motor."
        ),
    ),
    CompatibilityRule(
        name="cable_carries_motor",
        kind_a=Kind.CABLE,
        kind_b=Kind.MOTOR,
        predicate=_cable_carries_motor,
        description=(
            f"La ampacidad del conductor debe ser >= {CABLE_SIZING_FACTOR:.0%} "
            f"de la corriente nominal del motor."
        ),
    ),
    CompatibilityRule(
        name="protection_covers_drive",
        kind_a=Kind.PROTECTION,
        kind_b=Kind.DRIVE,
        predicate=_protection_covers_drive,
        description="La proteccion debe soportar la corriente de entrada del variador.",
    ),
)


def rules_for(a: Component, b: Component) -> list[CompatibilityRule]:
    """Reglas que gobiernan este par concreto de componentes."""
    return [r for r in COMPATIBILITY_RULES if r.applies_to(a, b)]


def is_compatible(a: Component, b: Component) -> bool:
    """True si el par no viola ninguna regla aplicable.

    Dos componentes sin regla en comun se consideran compatibles: la ausencia
    de restriccion no es una prohibicion.
    """
    return all(r.holds(a, b) for r in rules_for(a, b))


def violated_rules(a: Component, b: Component) -> list[CompatibilityRule]:
    """Reglas concretas que este par incumple. Es la evidencia que ve el cliente."""
    return [r for r in rules_for(a, b) if not r.holds(a, b)]
