"""Interfaz normalizada de LLM.

El loop del agente NO conoce a Gemini. Habla este contrato. Cambiar de
proveedor = escribir un archivo nuevo en app/llm/, sin tocar el agente, las
tools ni el solver.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol

Role = Literal["user", "assistant", "tool"]


@dataclass
class ToolCall:
    """Peticion del modelo para ejecutar una herramienta."""

    id: str
    name: str
    arguments: dict


@dataclass
class Message:
    """Turno de conversacion en formato agnostico al proveedor."""

    role: Role
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    # Solo para role="tool":
    tool_call_id: str | None = None
    tool_name: str | None = None


@dataclass
class LLMResponse:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)

    @property
    def wants_tools(self) -> bool:
        return bool(self.tool_calls)


@dataclass
class ToolSchema:
    """Declaracion de una herramienta en JSON Schema (formato comun)."""

    name: str
    description: str
    parameters: dict


class LLMProvider(Protocol):
    """Contrato minimo que debe cumplir cualquier proveedor."""

    name: str

    def complete(
        self,
        system: str,
        messages: list[Message],
        tools: list[ToolSchema],
    ) -> LLMResponse:
        ...
