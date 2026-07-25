"""Emision de cotizaciones — la unica ACCION del agente.

Todo lo demas que hace el sistema es leer y calcular. Esto escribe: consume un
consecutivo, genera un documento y lo deja en disco. Es la diferencia entre un
agente que responde y un agente que hace algo.

Se mantiene fuera de tools.py a proposito: `tools.py` es la frontera entre el
modelo y la verdad, y conviene que no acumule tambien la logica de un
documento comercial.

Los importes NO se recalculan en ningun punto posterior: el documento emitido
es la fuente. El LLM solo lee de aqui.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.graph.schema import Configuration, SOLUTION_SLOTS

QUOTES_DIR = Path("data/generated/quotes")
LEDGER = QUOTES_DIR / "ledger.jsonl"

# Validez comercial de una cotizacion. Es un supuesto declarado, no un dato:
# se expone en el documento para que el cliente lo vea.
VALIDITY_DAYS = 15


class QuoteBook:
    """Consecutivo + persistencia. Serializado: dos /chat concurrentes no
    pueden llevarse el mismo numero."""

    def __init__(self, directory: Path = QUOTES_DIR):
        self._dir = directory
        self._lock = threading.Lock()

    def _next_number(self) -> str:
        """COT-AAAAMM-NNNN. El consecutivo se deriva del ledger en disco, asi
        que sobrevive a un reinicio en medio de la demo."""
        period = datetime.now(timezone.utc).strftime("%Y%m")
        count = 0
        if LEDGER.exists():
            with LEDGER.open("r", encoding="utf-8") as fh:
                count = sum(1 for line in fh if f'"COT-{period}-' in line)
        return f"COT-{period}-{count + 1:04d}"

    def issue(
        self,
        config: Configuration,
        customer_name: str = "Cliente",
        notes: str = "",
        objective_key: str = "balanced",
        session_id: str = "default",
    ) -> dict:
        now = datetime.now(timezone.utc)

        items = [
            {
                "posicion": i,
                "tipo": kind.value,
                "id": config.components[kind].id,
                "descripcion": config.components[kind].name,
                "cantidad": 1,
                "precio_unitario_cop": config.components[kind].price_cop,
                "disponibilidad": config.components[kind].stock,
            }
            for i, kind in enumerate((k for k in SOLUTION_SLOTS if k in config.components), 1)
        ]

        with self._lock:
            self._dir.mkdir(parents=True, exist_ok=True)
            number = self._next_number()

            quote = {
                "numero": number,
                "cliente": customer_name or "Cliente",
                "emitida": now.isoformat(),
                "valida_hasta": (now + timedelta(days=VALIDITY_DAYS)).isoformat(),
                "validez_dias": VALIDITY_DAYS,
                "items": items,
                "total_cop": config.total_price_cop,
                "observaciones": notes,
                # Trazabilidad: con que politica comercial activa se cotizo y en
                # que conversacion. Sin esto una cotizacion no es auditable.
                "objetivo_de_negocio": objective_key,
                "session_id": session_id,
                "moneda": "COP",
            }

            path = self._dir / f"{number}.json"
            path.write_text(
                json.dumps(quote, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            with LEDGER.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(quote, ensure_ascii=False) + "\n")

        quote["archivo"] = str(path)
        return quote

    def all(self) -> list[dict]:
        if not LEDGER.exists():
            return []
        with LEDGER.open("r", encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def get(self, number: str) -> dict | None:
        return next((q for q in self.all() if q["numero"] == number), None)


quotes = QuoteBook()
