"""Troceo de documentacion tecnica en fragmentos citables.

Un chunk existe para ser CITADO: por eso siempre carga documento y pagina. Si
un fragmento no se puede citar, no sirve — el agente no debe afirmar nada que
el jurado no pueda abrir y verificar.

QUE SE INDEXA Y QUE NO:
Las filas de tabla de seleccion (numero de parte, kW, amperios, precio) NO se
indexan: esos datos ya viven en el grafo, donde son estructurados y exactos.
Duplicarlos en el indice vectorial seria invitar al agente a leer un precio de
un texto recuperado en vez de del catalogo — justo el error que este proyecto
existe para evitar. Aqui va solo la prosa: instalacion, derating, normas,
condiciones de garantia.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# Filas de tabla de seleccion de WEG. Duplica el patron de
# scripts/ingest_weg.py a proposito: app/ no debe importar de scripts/, y esta
# copia solo necesita RECONOCER filas para descartarlas, no parsearlas.
_TABLE_ROW = re.compile(r"(?:CFW|SSW|W22|CWB|MPW)[A-Z0-9-]*\s.*\$\s?[\d,]+")

# Codigos de producto mencionados en prosa: sirven para enlazar el fragmento
# con nodos del grafo.
_PRODUCT_CODE = re.compile(r"\b(?:CFW|SSW|W22|CWB|MPW)[A-Z0-9-]{2,}\b", re.IGNORECASE)

MAX_CHARS = 900
OVERLAP_CHARS = 120
MIN_CHARS = 80


@dataclass
class Chunk:
    """Fragmento indexable. `meta` es libre y viaja como JSON en Chroma."""

    text: str
    source: str
    page: int = 0
    component_ids: list[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    @property
    def id(self) -> str:
        """ID determinista: reindexar el mismo PDF actualiza en vez de duplicar.

        `meta` entra en la huella porque los perfiles de aplicacion guardan ahi
        sus restricciones: editar un `suggests` sin tocar el texto debe forzar
        la reindexacion, o el indice sirve sugerencias viejas en silencio.
        """
        payload = f"{self.source}|{self.page}|{self.text}|{json.dumps(self.meta, sort_keys=True)}"
        digest = hashlib.blake2b(payload.encode(), digest_size=12).hexdigest()
        return f"{self.source}:{self.page}:{digest}"

    # Chroma solo admite escalares en metadata: las listas y dicts se serializan.
    def to_metadata(self) -> dict:
        return {
            "source": self.source,
            "page": self.page,
            "component_ids": ",".join(self.component_ids),
            "meta_json": json.dumps(self.meta, ensure_ascii=False),
        }

    @classmethod
    def from_record(cls, document: str, metadata: dict) -> "Chunk":
        raw_ids = metadata.get("component_ids") or ""
        return cls(
            text=document,
            source=metadata.get("source", "?"),
            page=int(metadata.get("page", 0)),
            component_ids=[i for i in raw_ids.split(",") if i],
            meta=json.loads(metadata.get("meta_json") or "{}"),
        )


# ------------------------------------------------------------------ troceo


def _is_table_line(line: str) -> bool:
    """True si la linea es una fila de tabla y no prosa.

    Se evalua LINEA A LINEA, no por bloque: pypdf casi nunca conserva las
    lineas en blanco entre parrafos, asi que a nivel de bloque la unidad
    minima seria la pagina entera — y una sola fila de tabla bastaria para
    tirar a la basura toda la prosa util de esa pagina.
    """
    if _TABLE_ROW.search(line):
        return True
    digits = sum(ch.isdigit() for ch in line)
    return digits / max(len(line), 1) > 0.30


def _split_long(text: str) -> list[str]:
    """Parte un bloque largo en ventanas con solapamiento, cortando en frases.

    El solapamiento evita que una condicion quede partida justo en la frontera
    ('...no aplica si' | 'la altitud supera 1000 m') y se pierda en ambos lados.
    """
    if len(text) <= MAX_CHARS:
        return [text]

    sentences = re.split(r"(?<=[.;:])\s+", text)
    windows: list[str] = []
    current = ""

    for sentence in sentences:
        if current and len(current) + len(sentence) + 1 > MAX_CHARS:
            windows.append(current.strip())
            current = current[-OVERLAP_CHARS:] + " " + sentence
        else:
            current = f"{current} {sentence}".strip()

    if current.strip():
        windows.append(current.strip())
    return windows


def _prose_blocks(text: str) -> list[str]:
    """Agrupa lineas consecutivas de prosa, usando tablas y vacios como corte.

    Recorrer linea a linea y cortar en cada fila de tabla logra dos cosas de
    una vez: descarta el ruido numerico y mantiene junta la prosa que lo rodea,
    aunque el PDF no traiga ninguna linea en blanco.
    """
    blocks: list[str] = []
    buffer: list[str] = []

    def flush() -> None:
        if buffer:
            blocks.append(" ".join(buffer))
            buffer.clear()

    for line in text.splitlines():
        line = line.strip()
        if not line or _is_table_line(line):
            flush()
        else:
            buffer.append(line)

    flush()
    return blocks


def chunks_from_pdf(path: Path, known_ids: set[str] | None = None) -> list[Chunk]:
    """Extrae fragmentos de prosa de un PDF, pagina por pagina.

    Se trocea por parrafo y no por ventana fija: las hojas de datos son notas
    tecnicas cortas y autocontenidas, y partir una nota de derating a la mitad
    produce un fragmento que miente por omision.
    """
    from pypdf import PdfReader

    known_ids = known_ids or set()
    reader = PdfReader(str(path))
    chunks: list[Chunk] = []

    for page_no, page in enumerate(reader.pages, start=1):
        for block in _prose_blocks(page.extract_text() or ""):
            for window in _split_long(block):
                if len(window) < MIN_CHARS:
                    continue
                mentioned = {m.upper() for m in _PRODUCT_CODE.findall(window)}
                chunks.append(Chunk(
                    text=window,
                    source=path.name,
                    page=page_no,
                    # Solo se enlazan codigos que existan de verdad en el grafo.
                    component_ids=sorted(
                        cid for cid in known_ids
                        if any(code in cid.upper() for code in mentioned)
                    ),
                ))

    return chunks
