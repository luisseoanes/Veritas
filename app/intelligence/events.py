"""Registro estructurado de interacciones.

Cada conversacion con un cliente es un evento de investigacion de mercado. Este
modulo es la capa de captura: convierte lo que pasa en la conversacion en datos
sobre los que los detectores pueden razonar.

Es tambien la primera capa del motor de aprendizaje. No pretendemos que el
sistema "aprenda" en una demo de 4 horas — pero todo lo necesario para hacerlo
queda registrado desde el primer minuto, y eso si es real.
"""
from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

EVENT_LOG = Path("data/generated/events.jsonl")


class EventType(str, Enum):
    SOLVED = "solved"        # Hubo solucion y el cliente vio una recomendacion
    UNMET = "unmet"          # NO hubo solucion — el evento mas valioso del sistema
    CONSULTED = "consulted"  # Componentes que entraron en consideracion


@dataclass
class Event:
    type: EventType
    session_id: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    # Requerimientos que pidio el cliente, normalizados.
    requirements: dict = field(default_factory=dict)
    # SOLVED: ids de la configuracion recomendada + componentes considerados.
    configuration: list[str] = field(default_factory=list)
    considered: list[str] = field(default_factory=list)
    total_price_cop: int = 0
    total_margin_cop: int = 0
    # UNMET: nombres de los requerimientos del nucleo insatisfacible.
    unsat_core: list[str] = field(default_factory=list)
    minimum_viable_cop: int | None = None
    business_objective: str = "balanced"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["type"] = self.type.value
        return d


class EventLog:
    """Almacen de eventos en memoria con persistencia JSONL.

    En memoria para que el dashboard sea instantaneo; en disco para que el
    historico sobreviva reinicios y sea auditable por el jurado.
    """

    def __init__(self, path: Path = EVENT_LOG):
        self._events: list[Event] = []
        self._path = path
        self._lock = threading.Lock()

    def record(self, event: Event) -> Event:
        with self._lock:
            self._events.append(event)
            self._append_to_disk(event)
        return event

    def _append_to_disk(self, event: Event) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

    def load_from_disk(self) -> int:
        """Recarga el historico. Devuelve cuantos eventos se leyeron."""
        if not self._path.exists():
            return 0
        loaded = []
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)
                raw["type"] = EventType(raw["type"])
                loaded.append(Event(**raw))
        with self._lock:
            self._events = loaded
        return len(loaded)

    def clear(self) -> None:
        with self._lock:
            self._events = []
            if self._path.exists():
                self._path.unlink()

    # ------------------------------------------------------------- consultas

    def all(self) -> list[Event]:
        with self._lock:
            return list(self._events)

    def of_type(self, event_type: EventType) -> list[Event]:
        return [e for e in self.all() if e.type is event_type]

    def __len__(self) -> int:
        return len(self._events)


# Instancia compartida por la aplicacion.
event_log = EventLog()
