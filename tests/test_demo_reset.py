"""B3 — POST /demo/reset devuelve el sistema al estado inicial entre ensayos.

Limpia memoria y trazas, recarga el grafo, vuelve el objetivo a 'balanced', y
—solo si keep_history=False— vacia el log de eventos del dashboard.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.agent.memory import memory
from app.agent.tracing import tracer
from app.config import settings
from app.intelligence.events import Event, EventType, event_log
from app.main import app

TOKEN = "token-de-prueba-1234"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(settings, "admin_token", TOKEN)
    return TestClient(app)


def _auth() -> dict:
    return {"X-Admin-Token": TOKEN}


def test_reset_exige_auth(client: TestClient) -> None:
    assert client.post("/demo/reset", json={}).status_code == 401


def test_reset_vuelve_el_objetivo_a_balanced(client: TestClient) -> None:
    client.post("/admin/objective", json={"key": "maximize_margin"}, headers=_auth())
    r = client.post("/demo/reset", json={"keep_history": True}, headers=_auth())
    assert r.status_code == 200
    assert r.json()["objetivo_activo"] == "balanced"


def test_reset_limpia_memoria_y_trazas(client: TestClient) -> None:
    memory.get("sesion-x").remember(power_kw=5)
    tracer.start("sesion-x")
    tracer.record("sesion-x", "tool", name="solve_configuration")
    assert memory.all_ids() and tracer.get("sesion-x")

    client.post("/demo/reset", json={}, headers=_auth())

    assert memory.all_ids() == []
    assert tracer.get("sesion-x") == []


def test_keep_history_por_defecto_conserva_eventos(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(event_log, "_path", tmp_path / "events.jsonl")
    event_log.record(Event(type=EventType.SOLVED, session_id="s"))
    antes = len(event_log)
    assert antes > 0

    client.post("/demo/reset", json={}, headers=_auth())  # keep_history default True

    assert len(event_log) == antes  # el historico no se toco


def test_sin_keep_history_borra_eventos(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(event_log, "_path", tmp_path / "events.jsonl")
    event_log.record(Event(type=EventType.SOLVED, session_id="s"))
    assert len(event_log) > 0

    client.post("/demo/reset", json={"keep_history": False}, headers=_auth())

    assert len(event_log) == 0
