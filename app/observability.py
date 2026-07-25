"""Logging estructurado y correlacion por request (B9).

Antes no habia ni una linea de log: depurar "por que ese /chat tardo" o "que
tool se llamo" a las 11 de la noche era imposible. Aqui se centraliza:

  - un `request_id` por request (ContextVar), que se inyecta en CADA log via un
    filtro, para poder seguir una peticion de punta a punta (incluido el turno
    del agente, que corre en el threadpool — anyio copia el contexto por tarea).
  - un formato de linea greppable `clave=valor` (no JSON: legible en la consola
    de la demo y facil de filtrar con grep/awk).

Se usa un ContextVar, no un parametro, por lo mismo que en tools.py: FastAPI
corre cada request en su propio contexto, asi que el id no hay que pasarlo a
mano por toda la cadena.
"""
from __future__ import annotations

import contextvars
import logging
import sys

# Id de la request en curso. "-" fuera de un request (arranque, scripts).
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="-"
)


class _RequestIdFilter(logging.Filter):
    """Inyecta el request_id vigente en cada LogRecord del logger 'reshapex'."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


_configured = False


def configure_logging(level: int = logging.INFO) -> None:
    """Configura el logger 'reshapex' una sola vez (idempotente).

    No toca el root logger para no pisar la configuracion de uvicorn; los logs
    de la app cuelgan de 'reshapex' y sus hijos ('reshapex.agent', ...).
    """
    global _configured
    if _configured:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] req=%(request_id)s %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    handler.addFilter(_RequestIdFilter())

    root = logging.getLogger("reshapex")
    root.setLevel(level)
    root.handlers = [handler]
    root.propagate = False  # no duplicar en el root logger
    _configured = True
