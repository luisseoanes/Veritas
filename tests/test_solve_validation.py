"""B8 — SolveRequest rechaza potencia, voltaje y presupuesto no positivos.

Sin esto, /solve aceptaba power_kw=-5 o budget_cop=0. Un jurado jugando con
/docs lo encontraria. La validacion vive en el modelo Pydantic, asi que FastAPI
devuelve 422 automaticamente (el chequeo a nivel HTTP lo cubre B10).

Se prueba a nivel de modelo para no levantar la app ni el indice vectorial.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.main import SolveRequest


@pytest.mark.parametrize(
    "payload",
    [
        {"power_kw": -5},
        {"power_kw": 0},
        {"budget_cop": 0},
        {"budget_cop": -1},
        {"voltage": -220},
        {"voltage": 0},
    ],
)
def test_rechaza_valores_no_positivos(payload: dict) -> None:
    with pytest.raises(ValidationError):
        SolveRequest(**payload)


def test_acepta_none_y_valores_validos() -> None:
    # Todos None: valido — /solve exige al menos un requerimiento aparte (400),
    # pero el modelo en si no obliga a ninguno.
    SolveRequest()
    # Valores realistas.
    req = SolveRequest(power_kw=7.5, voltage=440, budget_cop=6_000_000)
    assert req.power_kw == 7.5 and req.voltage == 440 and req.budget_cop == 6_000_000
