"""Memoria de conversacion por sesion.

Guarda el historial y el estado acumulado del cliente (lo que ya dijo, lo que
ya se descarto). Sin esto el agente vuelve a preguntar el voltaje en cada turno
y la conversacion no progresa.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.llm.base import Message


@dataclass
class Session:
    session_id: str
    history: list[Message] = field(default_factory=list)
    # Requerimientos acumulados a lo largo de la conversacion.
    known: dict = field(default_factory=dict)
    # Configuraciones que el cliente ya rechazo (no volver a proponerlas).
    discarded: list[tuple[str, ...]] = field(default_factory=list)

    def add(self, message: Message) -> None:
        self.history.append(message)

    def remember(self, **facts) -> None:
        """Acumula hechos no nulos del cliente entre turnos."""
        self.known.update({k: v for k, v in facts.items() if v is not None})

    def discard(self, configuration_ids: tuple[str, ...]) -> None:
        if configuration_ids not in self.discarded:
            self.discarded.append(configuration_ids)

    def summary(self) -> str:
        """Contexto compacto que se inyecta al system prompt."""
        if not self.known:
            return "Aun no se conoce ningun requerimiento del cliente."
        parts = [f"{k}={v}" for k, v in self.known.items()]
        text = "Requerimientos ya conocidos: " + ", ".join(parts)
        if self.discarded:
            text += f"\nConfiguraciones ya descartadas por el cliente: {self.discarded}"
        return text


class MemoryStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def get(self, session_id: str) -> Session:
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(session_id=session_id)
        return self._sessions[session_id]

    def reset(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def reset_all(self) -> None:
        """Borra todas las sesiones. Lo usa /demo/reset para arrancar limpio."""
        self._sessions.clear()

    def all_ids(self) -> list[str]:
        return list(self._sessions)


memory = MemoryStore()
