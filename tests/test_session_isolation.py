"""Regresion de B6 — la sesion del agente esta aislada por request.

Antes, la sesion en curso era un dict global mutable. run_agent() hace varias
llamadas de red al LLM entre set_session() y el momento en que una tool lee el
id; con dos /chat concurrentes, el segundo pisaba el id del primero y los
eventos quedaban mal atribuidos.

Este test reproduce esa ventana: cada 'request' fija su id, cede el control un
instante (simulando las llamadas de red) y luego lee. Con el dict global fallaba;
con contextvars.ContextVar —que se copia por hilo/tarea— cada uno ve el suyo.
"""
from __future__ import annotations

import threading
import time

from app.agent.tools import _current_session, set_session


def _simulate_request(session_id: str, work_seconds: float, out: dict) -> None:
    set_session(session_id)
    # Ventana donde el bug se manifestaba: entre fijar la sesion y leerla, el
    # agente hace trabajo (llamadas al LLM). Otro request corre en el medio.
    time.sleep(work_seconds)
    out[session_id] = _current_session.get()


def test_concurrent_sessions_do_not_bleed() -> None:
    out: dict[str, str] = {}
    # 'A' tarda mas: 'B' arranca y termina en medio de la ventana de 'A'. Con el
    # dict global, 'A' leeria "B". Con contextvars, cada hilo tiene su contexto.
    threads = [
        threading.Thread(target=_simulate_request, args=("A", 0.20, out)),
        threading.Thread(target=_simulate_request, args=("B", 0.05, out)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert out == {"A": "A", "B": "B"}, f"Las sesiones se mezclaron: {out}"


def test_default_outside_request() -> None:
    """Fuera de un request (contexto limpio), la sesion cae al default."""
    out: dict[str, str] = {}

    def _read_default() -> None:
        # Hilo nuevo = contexto nuevo, sin set_session previo.
        out["value"] = _current_session.get()

    t = threading.Thread(target=_read_default)
    t.start()
    t.join()

    assert out["value"] == "default"
