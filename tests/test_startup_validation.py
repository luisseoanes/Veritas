"""B5 — la app falla al arrancar si la configuracion no sirve.

Antes estos fallos aparecian tarde: el LLM en gemini sin key reventaba en el
primer /chat, y un ADMIN_TOKEN vacio dejaba el panel abierto sin que nadie se
enterara. _validate_config los convierte en un fallo de arranque.
"""
from __future__ import annotations

import pytest

from app.config import settings
from app.main import _validate_config


def _set(monkeypatch: pytest.MonkeyPatch, **kwargs: str) -> None:
    for key, value in kwargs.items():
        monkeypatch.setattr(settings, key, value)


def test_config_valida_no_revienta(monkeypatch: pytest.MonkeyPatch) -> None:
    _set(monkeypatch, llm_provider="mock", embedding_provider="", admin_token="un-token")
    _validate_config()  # no debe lanzar


def test_gemini_sin_key_revienta(monkeypatch: pytest.MonkeyPatch) -> None:
    _set(monkeypatch, llm_provider="gemini", gemini_api_key="", admin_token="un-token")
    with pytest.raises((ValueError, RuntimeError)):
        _validate_config()


def test_embedding_gemini_sin_key_revienta(monkeypatch: pytest.MonkeyPatch) -> None:
    # LLM en mock pero embeddings en gemini sin key: tambien debe fallar.
    _set(
        monkeypatch,
        llm_provider="mock",
        embedding_provider="gemini",
        gemini_api_key="",
        admin_token="un-token",
    )
    with pytest.raises(RuntimeError):
        _validate_config()


def test_admin_token_vacio_revienta(monkeypatch: pytest.MonkeyPatch) -> None:
    _set(monkeypatch, llm_provider="mock", embedding_provider="", admin_token="")
    with pytest.raises(RuntimeError):
        _validate_config()
