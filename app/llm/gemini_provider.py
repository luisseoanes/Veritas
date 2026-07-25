"""Proveedor Gemini (SDK google-genai).

Se desactiva el "automatic function calling" del SDK a proposito: el loop de
herramientas es nuestro (app/agent/loop.py) porque necesitamos trazar cada
decision del agente para poder defenderla ante el jurado. Delegar el loop al
SDK nos dejaria sin esa traza.
"""
from __future__ import annotations

import uuid

from google import genai
from google.genai import types

from app.llm.base import LLMResponse, Message, ToolCall, ToolSchema


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY vacio. Ponlo en .env o usa LLM_PROVIDER=mock."
            )
        self._client = genai.Client(api_key=api_key)
        self._model = model

    # ------------------------------------------------------------ conversion

    @staticmethod
    def _to_contents(messages: list[Message]) -> list[types.Content]:
        """Traduce el historial normalizado al formato de Gemini.

        Gemini usa role='model' para el asistente y entrega los resultados de
        herramientas dentro de un turno con role='user'.
        """
        contents: list[types.Content] = []

        for msg in messages:
            if msg.role == "user":
                contents.append(
                    types.Content(role="user", parts=[types.Part.from_text(text=msg.content)])
                )

            elif msg.role == "assistant":
                parts: list[types.Part] = []
                if msg.content:
                    parts.append(types.Part.from_text(text=msg.content))
                for call in msg.tool_calls:
                    parts.append(
                        types.Part.from_function_call(name=call.name, args=call.arguments)
                    )
                if parts:
                    contents.append(types.Content(role="model", parts=parts))

            elif msg.role == "tool":
                contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_function_response(
                                name=msg.tool_name or "unknown",
                                response={"result": msg.content},
                            )
                        ],
                    )
                )

        return contents

    @staticmethod
    def _to_tools(tools: list[ToolSchema]) -> list[types.Tool]:
        """`parameters_json_schema` acepta JSON Schema crudo, que es el formato
        en que declaramos las tools — evita traducir a types.Schema a mano."""
        if not tools:
            return []
        declarations = [
            types.FunctionDeclaration(
                name=t.name,
                description=t.description,
                parameters_json_schema=t.parameters,
            )
            for t in tools
        ]
        return [types.Tool(function_declarations=declarations)]

    # ---------------------------------------------------------------- llamada

    def complete(
        self,
        system: str,
        messages: list[Message],
        tools: list[ToolSchema],
    ) -> LLMResponse:
        config = types.GenerateContentConfig(
            system_instruction=system,
            tools=self._to_tools(tools),
            # El loop es nuestro: ver docstring del modulo.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )

        response = self._client.models.generate_content(
            model=self._model,
            contents=self._to_contents(messages),
            config=config,
        )

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []

        candidates = response.candidates or []
        if candidates and candidates[0].content and candidates[0].content.parts:
            for part in candidates[0].content.parts:
                if getattr(part, "function_call", None):
                    fc = part.function_call
                    tool_calls.append(
                        ToolCall(
                            id=fc.id or f"call_{uuid.uuid4().hex[:8]}",
                            name=fc.name,
                            arguments=dict(fc.args or {}),
                        )
                    )
                elif getattr(part, "text", None):
                    text_parts.append(part.text)

        return LLMResponse(text="".join(text_parts).strip(), tool_calls=tool_calls)
