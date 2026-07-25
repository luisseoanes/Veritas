"""Traza de decisiones del agente.

Registra cada paso: que pidio el modelo, con que argumentos, que devolvio la
herramienta. Es la evidencia que se muestra al jurado para responder la
pregunta inevitable — "esto funciona de verdad o esta mockeado?".
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


@dataclass
class TraceStep:
    step: int
    kind: str  # "llm" | "tool"
    detail: dict = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class Tracer:
    def __init__(self) -> None:
        self._traces: dict[str, list[TraceStep]] = {}

    def start(self, session_id: str) -> None:
        self._traces[session_id] = []

    def record(self, session_id: str, kind: str, **detail) -> None:
        steps = self._traces.setdefault(session_id, [])
        steps.append(TraceStep(step=len(steps) + 1, kind=kind, detail=detail))

    def get(self, session_id: str) -> list[dict]:
        return [asdict(s) for s in self._traces.get(session_id, [])]

    def clear(self, session_id: str) -> None:
        self._traces.pop(session_id, None)

    def clear_all(self) -> None:
        """Borra todas las trazas. Lo usa /demo/reset para arrancar limpio."""
        self._traces.clear()


tracer = Tracer()
