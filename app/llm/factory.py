"""Seleccion del proveedor de LLM segun configuracion."""
from __future__ import annotations

from app.config import settings
from app.llm.base import LLMProvider
from app.llm.mock_provider import MockProvider


def get_provider(name: str | None = None) -> LLMProvider:
    """Devuelve el proveedor activo. `name` permite forzarlo en pruebas."""
    provider = (name or settings.llm_provider).lower()

    if provider == "mock":
        return MockProvider()

    if provider == "gemini":
        # Import diferido: no exigimos el SDK instalado para correr en modo mock.
        from app.llm.gemini_provider import GeminiProvider

        return GeminiProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )

    raise ValueError(
        f"Proveedor de LLM desconocido: '{provider}'. Usa 'mock' o 'gemini'."
    )
