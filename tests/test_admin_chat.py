"""C5 — chatbot admin sobre el mismo motor (dual chatbot, docs/03).

Cubre las cuatro garantias de docs/03 §7, sin depender de un LLM real:
  1. Auth: /admin/chat cerrado por token; /chat sigue abierto.
  2. Separacion de perfiles: el admin no ve `solve_configuration`, el cliente no
     ve las tools de admin (verificable comparando conjuntos, sin red).
  3. El admin NO contamina el log de mercado: una vuelta de /admin/chat no crea
     eventos SOLVED/UNMET (solo `solve_configuration` los registra, y el perfil
     admin no la tiene).
  4. `set_business_objective` valida contra los 4 presets: cambia el estado con
     uno valido y revienta (sin cambiarlo) con uno desconocido.

TestClient sin context manager, igual que test_auth: no dispara el lifespan, asi
estos tests no tocan la capa de retrieval.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.agent.admin_tools import set_business_objective
from app.agent.loop import ADMIN, CLIENTE
from app.config import settings
from app.intelligence.events import EventType, event_log
from app.main import app
from app.state import state

TOKEN = "token-de-prueba-1234"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(settings, "admin_token", TOKEN)
    return TestClient(app)


# --------------------------------------------------------------------- 1. auth


def test_admin_chat_sin_token_da_401(client: TestClient) -> None:
    r = client.post("/admin/chat", json={"message": "hola", "session_id": "t"})
    assert r.status_code == 401


def test_admin_chat_con_token_da_200(client: TestClient) -> None:
    r = client.post(
        "/admin/chat",
        json={"message": "¿que oportunidades hay?", "session_id": "t"},
        headers={"X-Admin-Token": TOKEN},
    )
    assert r.status_code == 200
    assert r.json()["reply"]  # hay respuesta redactada


def test_chat_cliente_sigue_abierto(client: TestClient) -> None:
    r = client.post("/chat", json={"message": "hola", "session_id": "t"})
    assert r.status_code == 200


# ---------------------------------------------------- 2. separacion de perfiles


def test_perfil_admin_no_incluye_solve_configuration() -> None:
    assert "solve_configuration" not in ADMIN.tool_names


def test_perfil_cliente_no_incluye_tools_admin() -> None:
    # Cero solape entre las dos audiencias.
    assert not (set(CLIENTE.tool_names) & set(ADMIN.tool_names))


# ------------------------------------------- 3. el admin no escribe en el log


def test_admin_chat_no_crea_eventos_solved_unmet(client: TestClient) -> None:
    before_solved = len(event_log.of_type(EventType.SOLVED))
    before_unmet = len(event_log.of_type(EventType.UNMET))

    # Un mensaje que, por el canal de cliente, dispararia el solver (y por tanto
    # un evento). Por /admin/chat no debe registrar nada: el perfil admin no
    # tiene `solve_configuration`, la unica tool que graba eventos.
    r = client.post(
        "/admin/chat",
        json={"message": "necesito 5 kW a 440V por 8 millones", "session_id": "t"},
        headers={"X-Admin-Token": TOKEN},
    )
    assert r.status_code == 200
    assert len(event_log.of_type(EventType.SOLVED)) == before_solved
    assert len(event_log.of_type(EventType.UNMET)) == before_unmet


# ------------------------------------------- 4. set_business_objective (escritura)


def test_set_business_objective_preset_valido_cambia_estado() -> None:
    previo = state.objective_key
    try:
        out = set_business_objective("maximize_margin")
        assert state.objective_key == "maximize_margin"
        assert out["activo"] == "maximize_margin"
    finally:
        state.set_objective(previo)  # no ensuciar el estado global para otros tests


def test_set_business_objective_desconocido_revienta_sin_cambiar() -> None:
    state.set_objective("balanced")
    with pytest.raises(ValueError):
        set_business_objective("inventado")
    # El estado no cambio: la validacion de state.set_objective bloqueo la escritura.
    assert state.objective_key == "balanced"
