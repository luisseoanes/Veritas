"""B2 — POST /admin/frontier: frontera de Pareto + eleccion por objetivo.

El test central no es "responde 200": es el **invariante del sistema**. Cada
objetivo de negocio elige un punto, y ese punto DEBE estar sobre la frontera —
nunca una solucion dominada. Ese es el argumento tecnico contra "estan
manipulando al cliente". Aqui se verifica mecanicamente.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.solver.pareto import BUSINESS_OBJECTIVES

TOKEN = "token-de-prueba-1234"
# Escenario con frontera de varios puntos y objetivos que eligen distinto.
SCENARIO = {"power_kw": 5, "voltage": 440}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(settings, "admin_token", TOKEN)
    return TestClient(app)


def _auth(token: str = TOKEN) -> dict:
    return {"X-Admin-Token": token}


def test_frontier_exige_auth(client: TestClient) -> None:
    assert client.post("/admin/frontier", json=SCENARIO).status_code == 401


def test_frontier_estructura(client: TestClient) -> None:
    r = client.post("/admin/frontier", json=SCENARIO, headers=_auth())
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "OK"
    assert body["frontera"], "la frontera no deberia estar vacia"
    assert set(body["elegida_por_objetivo"]) == set(BUSINESS_OBJECTIVES)


def test_cada_objetivo_elige_dentro_de_la_frontera(client: TestClient) -> None:
    """EL invariante: ningun objetivo puede elegir una solucion dominada."""
    body = client.post("/admin/frontier", json=SCENARIO, headers=_auth()).json()

    frontera_ids = {tuple(c["ids"]) for c in body["frontera"]}
    dominadas_ids = {tuple(c["ids"]) for c in body["dominadas"]}

    # Frontera y dominadas son disjuntas.
    assert frontera_ids.isdisjoint(dominadas_ids)

    # Cada punto elegido esta SOBRE la frontera, nunca fuera.
    for key, elegida in body["elegida_por_objetivo"].items():
        assert tuple(elegida["ids"]) in frontera_ids, (
            f"El objetivo '{key}' eligio una solucion fuera de la frontera: {elegida['ids']}"
        )


def test_frontier_sin_solucion(client: TestClient) -> None:
    """Escenario imposible -> SIN_SOLUCION con nucleo insatisfacible."""
    imposible = {"power_kw": 5, "budget_cop": 1}  # presupuesto absurdo
    body = client.post("/admin/frontier", json=imposible, headers=_auth()).json()
    assert body["status"] == "SIN_SOLUCION"
    assert body["nucleo_insatisfacible"], "deberia listar las restricciones culpables"
