"""Indice vectorial sobre Chroma (persistente en disco).

DOS DECISIONES QUE IMPORTAN:

1. Chroma NUNCA calcula los embeddings. Las colecciones se crean con
   `embedding_function=None` y tanto la indexacion como la consulta reciben los
   vectores ya calculados por app/retrieval/embedder.py. Si se deja que Chroma
   elija su funcion por defecto, descarga un modelo ONNX de ~80 MB la primera
   vez que se usa — en la demo eso es un cuelgue de un minuto, o un fallo seco
   si la sala no tiene internet. Ademas asi el proveedor de embeddings queda en
   un solo sitio.

2. La coleccion recuerda con QUE embedder fue construida. Indexar con `mock` y
   consultar con `gemini` no falla: devuelve resultados silenciosamente
   absurdos. Al detectar el cambio, el indice se reconstruye en vez de mentir.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import chromadb
from chromadb.api.models.Collection import Collection

from app.retrieval.chunks import Chunk
from app.retrieval.embedder import Embedder


def _fingerprint(chunks: list[Chunk]) -> str:
    """Huella del contenido: cambia si cambia cualquier fragmento."""
    digest = hashlib.blake2b(digest_size=12)
    for chunk in sorted(c.id for c in chunks):
        digest.update(chunk.encode())
    return digest.hexdigest()


class VectorIndex:
    """Una coleccion de Chroma con su embedder asociado."""

    def __init__(
        self,
        client: chromadb.ClientAPI,
        name: str,
        embedder: Embedder,
        min_score: float | None = None,
    ):
        self._client = client
        self._name = name
        self._embedder = embedder
        # Umbral propio del corpus: ver el comentario del protocolo Embedder
        # sobre por que no puede ser uno solo para todos.
        self.min_score = (
            embedder.default_min_score if min_score is None else min_score
        )
        self._collection: Collection | None = None

    # ------------------------------------------------------------- coleccion

    @property
    def _stamp(self) -> str:
        """Identidad del espacio vectorial. Distinto stamp = indice incompatible."""
        return f"{self._embedder.name}:{self._embedder.dim}"

    def _metadata(self, extra: dict | None = None) -> dict:
        return {"hnsw:space": "cosine", "embedder_stamp": self._stamp, **(extra or {})}

    def _drop(self) -> None:
        """Borra la coleccion si existe. Chroma lanza si no existe."""
        try:
            self._client.delete_collection(self._name)
        except Exception:
            pass
        self._collection = None

    @property
    def collection(self) -> Collection:
        if self._collection is not None:
            return self._collection

        collection = self._client.get_or_create_collection(
            name=self._name,
            embedding_function=None,  # ver docstring del modulo
            metadata=self._metadata(),
        )

        # La coleccion ya existia con otro embedder: sus vectores no son
        # comparables con los que produciriamos ahora. Se descarta.
        if collection.metadata.get("embedder_stamp") != self._stamp:
            self._drop()
            collection = self._client.create_collection(
                name=self._name,
                embedding_function=None,
                metadata=self._metadata(),
            )

        self._collection = collection
        return collection

    def count(self) -> int:
        return self.collection.count()

    @property
    def content_fingerprint(self) -> str | None:
        return self.collection.metadata.get("content_fingerprint")

    # ------------------------------------------------------------- escritura

    def add(self, chunks: list[Chunk]) -> int:
        """Inserta o actualiza. El id del Chunk es determinista, asi que
        reindexar el mismo documento actualiza en vez de duplicar."""
        if not chunks:
            return 0

        embeddings = self._embedder.embed([c.text for c in chunks])
        self.collection.upsert(
            ids=[c.id for c in chunks],
            embeddings=embeddings.tolist(),
            documents=[c.text for c in chunks],
            metadatas=[c.to_metadata() for c in chunks],
        )
        return len(chunks)

    def reset(self) -> None:
        """Vacia la coleccion. La siguiente lectura la recrea vacia."""
        self._drop()

    def sync(self, chunks: list[Chunk]) -> bool:
        """Reconstruye solo si el contenido cambio. Devuelve True si reindexo.

        Importa por dinero y por tiempo: con el proveedor Gemini, reindexar es
        una llamada de red en cada arranque de la API. Con la huella, solo se
        paga cuando el corpus cambio de verdad.
        """
        if self.count() > 0 and self.content_fingerprint == _fingerprint(chunks):
            return False

        # No basta con upsert: si se BORRO un fragmento del corpus, seguiria
        # vivo en la coleccion. Se reconstruye desde cero.
        #
        # La huella se graba al CREAR y no con collection.modify(): Chroma
        # rechaza cualquier modify cuya metadata mencione la funcion de
        # distancia, y la metadata de modify reemplaza a la anterior completa.
        self._drop()
        self._collection = self._client.create_collection(
            name=self._name,
            embedding_function=None,
            metadata=self._metadata({"content_fingerprint": _fingerprint(chunks)}),
        )
        self.add(chunks)
        return True

    # -------------------------------------------------------------- consulta

    def search(
        self,
        query: str,
        k: int = 4,
        min_score: float | None = None,
    ) -> list[tuple[Chunk, float]]:
        """Devuelve (fragmento, similitud coseno) por encima del umbral.

        El umbral es deliberado: preferimos NO devolver nada a devolver algo
        irrelevante. Una lista vacia hace que el agente diga "no tengo
        respaldo"; un fragmento malo lo hace afirmar con confianza algo falso.
        """
        available = self.count()
        if available == 0:
            return []

        threshold = self.min_score if min_score is None else min_score
        vector = self._embedder.embed([query], query=True)[0]

        result = self.collection.query(
            query_embeddings=[vector.tolist()],
            n_results=min(k, available),
            include=["documents", "metadatas", "distances"],
        )

        hits: list[tuple[Chunk, float]] = []
        for document, metadata, distance in zip(
            result["documents"][0], result["metadatas"][0], result["distances"][0]
        ):
            # Espacio coseno: distancia = 1 - similitud.
            score = 1.0 - float(distance)
            if score >= threshold:
                hits.append((Chunk.from_record(document, metadata), score))
        return hits


# --------------------------------------------------------------- contenedor


DATASHEETS = "weg_datasheets"
PROFILES = "application_profiles"


class Retrieval:
    """Las dos colecciones del sistema, sobre un unico cliente de Chroma.

    Se mantienen separadas a proposito: son corpus con proposito, umbral y
    ciclo de vida distintos. Mezclarlas haria que una nota de instalacion
    compita en el ranking con un perfil de aplicacion.
    """

    def __init__(self, path: str | Path, embedder: Embedder):
        Path(path).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(path))
        self.embedder = embedder
        self.datasheets = VectorIndex(
            self._client, DATASHEETS, embedder,
            min_score=embedder.long_text_min_score,
        )
        self.profiles = VectorIndex(
            self._client, PROFILES, embedder,
            min_score=embedder.default_min_score,
        )

    def bootstrap_profiles(self) -> bool:
        """Indexa el corpus curado de perfiles. Idempotente."""
        from app.retrieval import profiles as profile_corpus

        return self.profiles.sync(profile_corpus.as_chunks())

    def stats(self) -> dict:
        return {
            "embedder": self.embedder.name,
            "dimensiones": self.embedder.dim,
            "perfiles_de_aplicacion": self.profiles.count(),
            "umbral_perfiles": self.profiles.min_score,
            "fragmentos_de_hojas_de_datos": self.datasheets.count(),
            "umbral_hojas_de_datos": self.datasheets.min_score,
        }
