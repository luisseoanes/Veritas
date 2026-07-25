"""Indexa hojas de datos de WEG en el indice vectorial (RAG).

Complementa a scripts/ingest_weg.py, que se queda con las TABLAS (datos
estructurados -> grafo). Este toma lo otro: la prosa tecnica que no cabe en un
grafo pero que el cliente pregunta — instalacion, derating, normas, garantia.

Uso:
    python -m scripts.index_datasheets --pdf data/raw/weg-drives.pdf
    python -m scripts.index_datasheets --url https://static.weg.net/...
    python -m scripts.index_datasheets --dir data/raw          # todos los PDF
    python -m scripts.index_datasheets --stats                 # que hay indexado
    python -m scripts.index_datasheets --reset                 # vaciar y empezar

El proveedor de embeddings sale de la configuracion: con EMBEDDING_PROVIDER o
LLM_PROVIDER en 'mock' el indice se construye sin API key (busqueda lexica),
con 'gemini' se construye con semantica real. El indice recuerda con cual se
construyo y se reconstruye solo si cambia.
"""
from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

from app.retrieval.chunks import chunks_from_pdf
from app.state import state

RAW_DIR = Path("data/raw")


def fetch(url: str) -> Path:
    """Descarga un PDF del Download Center. static.weg.net no bloquea bots."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dest = RAW_DIR / Path(url.split("?")[0]).name
    print(f"Descargando {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request) as response, dest.open("wb") as fh:
        fh.write(response.read())
    print(f"  -> {dest} ({dest.stat().st_size / 1_000_000:.1f} MB)")
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description="Indexa hojas de datos WEG para RAG")
    parser.add_argument("--pdf", type=Path, action="append", default=[])
    parser.add_argument("--url", action="append", default=[])
    parser.add_argument("--dir", type=Path, help="Indexa todos los PDF de una carpeta")
    parser.add_argument("--reset", action="store_true", help="Vacia el indice antes")
    parser.add_argument("--stats", action="store_true", help="Solo mostrar estado")
    args = parser.parse_args()

    retrieval = state.retrieval

    if args.stats:
        print("Estado del indice vectorial:")
        for key, value in retrieval.stats().items():
            print(f"  {key:<34} {value}")
        return

    paths: list[Path] = list(args.pdf)
    paths += [fetch(url) for url in args.url]
    if args.dir:
        paths += sorted(args.dir.glob("*.pdf"))

    if not paths and not args.reset:
        parser.error("Indica --pdf, --url, --dir, --reset o --stats")

    if args.reset:
        retrieval.datasheets.reset()
        print("Indice de hojas de datos vaciado.")
        if not paths:
            return

    total = 0
    for path in paths:
        if not path.exists():
            print(f"  [OMITIDO] no existe: {path}")
            continue

        # Solo se enlazan codigos que existan de verdad como nodos del grafo:
        # una cita que apunta a un producto inexistente no es trazable.
        chunks = chunks_from_pdf(path, known_ids={c.id for c in state.graph.all()})
        added = retrieval.datasheets.add(chunks)
        total += added

        pages = len({c.page for c in chunks})
        linked = sum(1 for c in chunks if c.component_ids)
        print(f"  {path.name}: {added} fragmentos de {pages} paginas "
              f"({linked} enlazados a componentes del grafo)")

        if added == 0:
            print("     Ningun fragmento util. Suele pasar con PDF que son solo "
                  "tablas o imagenes escaneadas (sin capa de texto).")

    print(f"\nTotal indexado en esta corrida: {total}")
    print("Estado del indice:")
    for key, value in retrieval.stats().items():
        print(f"  {key:<34} {value}")


if __name__ == "__main__":
    main()
