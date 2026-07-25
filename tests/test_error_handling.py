"""B7 — toda respuesta de error usa el mismo envelope {"error": {...}}.

Y lo mas importante: una excepcion no prevista devuelve un 500 limpio, sin
filtrar el stacktrace ni el mensaje interno al cliente.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

TOKEN = "token-de-prueba-1234"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(settings, "admin_token", TOKEN)
    # raise_server_exceptions=False: queremos ver la respuesta 500 que produce
    # el handler, no que el TestClient re-lance la excepcion.
    return TestClient(app, raise_server_exceptions=False)


def test_http_exception_usa_envelope(client: TestClient) -> None:
    # require_stock=False y sin ningun otro campo -> cero requerimientos -> 400.
    # (Con {} el modelo pone require_stock=True, asi que si habria uno.)
    r = client.post("/solve", json={"require_stock": False})
    assert r.status_code == 400
    assert set(r.json()) == {"error"}
    assert r.json()["error"]["status"] == 400


def test_validacion_usa_envelope(client: TestClient) -> None:
    r = client.post("/solve", json={"power_kw": -5})  # 422
    assert r.status_code == 422
    body = r.json()["error"]
    assert body["status"] == 422
    assert body["detalles"], "deberia listar el campo invalido"


def test_401_usa_envelope(client: TestClient) -> None:
    r = client.post("/admin/objective", json={"key": "balanced"})
    assert r.status_code == 401
    assert r.json()["error"]["status"] == 401


def test_excepcion_no_manejada_da_500_sin_filtrar(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(*args, **kwargs):
        raise RuntimeError("detalle-interno-secreto")

    monkeypatch.setattr("app.main.solve", boom)
    r = client.post("/solve", json={"power_kw": 7.5, "voltage": 440})

    assert r.status_code == 500
    assert r.json()["error"]["status"] == 500
    # No se filtra el detalle interno al cliente.
    assert "detalle-interno-secreto" not in r.text
