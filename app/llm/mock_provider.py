"""Proveedor simulado — SOLO para desarrollo y pruebas sin API key.

Por que existe y por que NO es "mockear el producto":
la logica de negocio de este sistema (grafo, solver, nucleo insatisfacible,
Pareto, detectores) no vive en el modelo. El LLM solo traduce lenguaje natural
a requerimientos y explica el resultado. Este proveedor sustituye esa traduccion
por reglas deterministas para poder correr y testear TODO el motor sin red.

En la demo se usa Gemini. Este archivo nunca debe ser el proveedor activo
cuando se muestra el sistema.
"""
from __future__ import annotations

import re
import uuid

from app.llm.base import LLMResponse, Message, ToolCall, ToolSchema

_KW = re.compile(r"(\d+(?:[.,]\d+)?)\s*k?w\b", re.IGNORECASE)
_VOLT = re.compile(r"(\d{3})\s*v\b", re.IGNORECASE)
_BUDGET = re.compile(r"(\d[\d.,']*)\s*(millones|millon|m\b|cop)", re.IGNORECASE)

_FEATURE_HINTS = {
    "soft_start": ("arranque suave", "soft start", "arranque"),
    "modbus": ("modbus",),
    "profibus": ("profibus",),
    "pid": ("pid", "control de lazo"),
    "ip66": ("ip66", "intemperie"),
}


def _parse_number(raw: str) -> float:
    return float(raw.replace(".", "").replace(",", "").replace("'", ""))


def _extract_requirements(text: str) -> dict:
    """Traduccion determinista texto -> requerimientos (lo que hace el LLM real)."""
    args: dict = {}

    if m := _KW.search(text):
        args["power_kw"] = float(m.group(1).replace(",", "."))
    if m := _VOLT.search(text):
        args["voltage"] = int(m.group(1))
    if m := _BUDGET.search(text):
        value = _parse_number(m.group(1))
        unit = m.group(2).lower()
        args["budget_cop"] = int(value * 1_000_000) if unit.startswith("millon") or unit == "m" else int(value)

    lowered = text.lower()
    features = [f for f, hints in _FEATURE_HINTS.items() if any(h in lowered for h in hints)]
    if features:
        args["features"] = features

    return args


class MockProvider:
    name = "mock"

    def complete(
        self,
        system: str,
        messages: list[Message],
        tools: list[ToolSchema],
    ) -> LLMResponse:
        tool_names = {t.name for t in tools}
        already_called = {
            call.name for m in messages if m.role == "assistant" for call in m.tool_calls
        }
        last_user = next(
            (m.content for m in reversed(messages) if m.role == "user"), ""
        )

        # Paso 1: traducir la necesidad a requerimientos y llamar al solver.
        if "solve_configuration" in tool_names and "solve_configuration" not in already_called:
            args = _extract_requirements(last_user)
            if args:
                return LLMResponse(
                    tool_calls=[
                        ToolCall(
                            id=f"call_{uuid.uuid4().hex[:8]}",
                            name="solve_configuration",
                            arguments=args,
                        )
                    ]
                )

        # Paso 2: ya hay resultado del solver -> resumirlo.
        tool_output = next(
            (m.content for m in reversed(messages) if m.role == "tool"), ""
        )
        if tool_output:
            return LLMResponse(
                text=(
                    "[proveedor simulado] El solver respondio:\n\n"
                    f"{tool_output}\n\n"
                    "Cambia LLM_PROVIDER=gemini en .env para obtener la explicacion "
                    "en lenguaje natural."
                )
            )

        return LLMResponse(
            text=(
                "[proveedor simulado] No pude extraer requerimientos del mensaje. "
                "Incluye potencia (kW), voltaje (V) y presupuesto."
            )
        )
