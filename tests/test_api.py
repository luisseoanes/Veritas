"""B10 — tests de API de punta a punta con TestClient.

Complementa (no duplica) los tests de auth/validacion/reset ya existentes. Aqui:
  - salud y contrato basico de /health,
  - el header X-Request-ID que añade el logging por request (B9),
  - /solve valido,
  - la CARRERA DE B6 a traves de /chat REAL: varias conversaciones concurrentes
    con session_id distintos, afirmando que cada evento queda atribuido a SU
    sesion (el bug original mezclaba los ids via un dict global).

El event_log se aisla en un archivo temporal por test: los /chat graban eventos
en disco, y no queremos tocar el historico real ni depender de su contenido.
"""
from __future__ import annotations

import threading

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.intelligence.events import event_log
from app.main import app

TOKEN = "token-de-prueba-1234"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path) -> TestClient:
    monkeypatch.setattr(settings, "admin_token", TOKEN)
    # Aislar el log de eventos: archivo temporal + memoria vacia.
    monkeypatch.setattr(event_log, "_path", tmp_path / "events.jsonl")
    monkeypatch.setattr(event_log, "_events", [])
    return TestClient(app)


# ------------------------------------------------------------------- salud


def test_health_ok(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "graph" in body and "objetivo_activo" in body


def test_request_id_en_header(client: TestClient) -> None:
    """B9: cada respuesta trae X-Request-ID para correlacionar logs."""
    r = client.get("/health")
    assert r.headers.get("X-Request-ID")


# ------------------------------------------------------------------- /solve


def test_solve_valido(client: TestClient) -> None:
    r = client.post("/solve", json={"power_kw": 7.5, "voltage": 440})
    assert r.status_code == 200


def test_admin_sin_token_da_401(client: TestClient) -> None:
    assert client.get("/admin/dashboard").status_code == 401


# --------------------------------------------- B6: atribucion bajo concurrencia


def test_chats_concurrentes_atribuyen_bien_los_eventos(client: TestClient) -> None:
    """Varios /chat en paralelo: cada evento debe quedar en SU sesion.

    Antes, `_current_session` era un dict global y dos /chat concurrentes se
    pisaban el id -> eventos mal atribuidos. Con el ContextVar (B6), cada request
    ve el suyo. La sesion se namespacea por perfil, asi que el id grabado es
    'cliente:<session_id>'.
    """
    ids = [f"sesion-{i}" for i in range(8)]
    msg = "necesito 5 kW a 440V por 8 millones"

    def fire(sid: str) -> None:
        client.post("/chat", json={"message": msg, "session_id": sid})

    threads = [threading.Thread(target=fire, args=(sid,)) for sid in ids]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    recorded = {e.session_id for e in event_log.all()}
    expected = {f"cliente:{sid}" for sid in ids}

    # Cada sesion produjo su evento y NINGUNO se atribuyo a otra (sin el fix, el
    # conjunto grabado seria menor o tendria ids cruzados).
    assert recorded == expected
