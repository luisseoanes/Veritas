"""B1 — auth de administrador por token compartido.

El cliente (chat, /solve) es abierto; el administrador exige el header
X-Admin-Token. Aqui se prueban las dos caras: que el admin queda cerrado sin
token valido, y que el cliente sigue abierto.

Se usa TestClient sin context manager a proposito: asi no se disparan los
handlers de arranque (no se construye el indice vectorial), y estos tests no
tocan la capa de retrieval.
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
    return TestClient(app)


# ------------------------------------------------------------------ admin cerrado


def test_admin_sin_token_da_401(client: TestClient) -> None:
    r = client.post("/admin/objective", json={"key": "maximize_margin"})
    assert r.status_code == 401


def test_admin_token_incorrecto_da_401(client: TestClient) -> None:
    r = client.post(
        "/admin/objective",
        json={"key": "maximize_margin"},
        headers={"X-Admin-Token": "incorrecto"},
    )
    assert r.status_code == 401


def test_admin_token_correcto_pasa(client: TestClient) -> None:
    r = client.post(
        "/admin/objective",
        json={"key": "maximize_margin"},
        headers={"X-Admin-Token": TOKEN},
    )
    assert r.status_code == 200
    assert r.json()["activo"] == "maximize_margin"
    # Limpieza: no dejar el objetivo global sucio para otros tests.
    client.post(
        "/admin/objective",
        json={"key": "balanced"},
        headers={"X-Admin-Token": TOKEN},
    )


# --------------------------------------------------------------------- login


def test_verify_es_el_login_del_front(client: TestClient) -> None:
    assert client.get("/admin/verify").status_code == 401
    ok = client.get("/admin/verify", headers={"X-Admin-Token": TOKEN})
    assert ok.status_code == 200 and ok.json() == {"ok": True}


# --------------------------------------------------------- cliente sigue abierto


def test_cliente_no_exige_token(client: TestClient) -> None:
    assert client.get("/health").status_code == 200
    r = client.post("/solve", json={"power_kw": 7.5, "voltage": 440})
    assert r.status_code == 200


# ----------------------------------------------------------------- fail-closed


def test_sin_token_configurado_niega_todo(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Si el servidor no tiene ADMIN_TOKEN, ni el token correcto entra."""
    monkeypatch.setattr(settings, "admin_token", "")
    r = client.get("/admin/verify", headers={"X-Admin-Token": "loquesea"})
    assert r.status_code == 500
