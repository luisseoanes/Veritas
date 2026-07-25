"""Registro de herramientas.

Agregar una tool = decorar una funcion con su JSON Schema. El registro produce
los `ToolSchema` que consume la capa LLM y ejecuta las llamadas del modelo.
"""
from __future__ import annotations

import json
import traceback
from dataclasses import dataclass
from typing import Any, Callable

from app.llm.base import ToolSchema


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    func: Callable[..., Any]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def tool(self, name: str, description: str, parameters: dict):
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._tools[name] = Tool(name, description, parameters, func)
            return func

        return decorator

    def schemas(self, only: list[str] | None = None) -> list[ToolSchema]:
        items = self._tools.values()
        if only is not None:
            items = [t for t in items if t.name in only]
        return [ToolSchema(t.name, t.description, t.parameters) for t in items]

    def names(self) -> list[str]:
        return list(self._tools)

    def execute(self, name: str, arguments: dict) -> str:
        """Ejecuta una tool y SIEMPRE devuelve string: es lo que espera el LLM.

        Los errores se devuelven como texto en vez de propagarse, para que el
        agente pueda reaccionar (reintentar con otros argumentos) en vez de
        tumbar la conversacion.
        """
        tool = self._tools.get(name)
        if tool is None:
            return f"ERROR: la herramienta '{name}' no existe."
        try:
            result = tool.func(**(arguments or {}))
            if isinstance(result, str):
                return result
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception:
            return f"ERROR ejecutando '{name}':\n{traceback.format_exc()}"


registry = ToolRegistry()
