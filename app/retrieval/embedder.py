"""Capa de embeddings, agnostica al proveedor.

Mismo contrato que app/llm: una interfaz, un mock y un proveedor real. Cambiar
de proveedor no toca ni el indice ni las tools.

POR QUE HAY UN MOCK Y POR QUE NO ES TRAMPA:
El mock no inventa resultados: es una bolsa de palabras con hashing determinista.
Degrada la busqueda semantica a busqueda por palabras — peor, pero real y
verificable. Eso permite que `scripts/smoke_test.py` compruebe el pipeline
completo de retrieval sin API key. En la demo se usa Gemini
(`LLM_PROVIDER=gemini`), donde si hay semantica de verdad.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Protocol

import numpy as np


class Embedder(Protocol):
    """Contrato minimo. `query=True` marca que el texto es una consulta y no un
    documento: los modelos modernos proyectan cada rol de forma distinta."""

    name: str
    dim: int

    # HAY DOS UMBRALES, Y NO ES UN PARCHE:
    # El coseno entre una pregunta corta y un fragmento largo es
    # estructuralmente mas bajo que entre dos textos de tamano parecido — el
    # documento reparte su norma entre muchos mas terminos. Un umbral unico
    # obliga a elegir entre dejar pasar ruido en el corpus corto o descartar
    # aciertos en el largo. Por eso cada corpus usa el suyo.
    #
    # `default_min_score`   -> textos cortos y homogeneos (perfiles, ~20 palabras)
    # `long_text_min_score` -> fragmentos de documentacion (~150 palabras)
    default_min_score: float
    long_text_min_score: float

    def embed(self, texts: list[str], *, query: bool = False) -> np.ndarray:
        ...


# --------------------------------------------------------------------- utils


def _normalize(vectors: np.ndarray) -> np.ndarray:
    """Normaliza a norma 1 para que el producto punto SEA el coseno."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.maximum(norms, 1e-9)


# Palabras vacias del espanol. Sin esto la bolsa de palabras del mock mide
# sobre todo "de/la/en/para" y dos textos sin nada en comun salen parecidos.
_STOPWORDS = frozenset(
    """a al algo algun alguna ante antes aqui asi con contra cual cuando cuanto
    de del desde donde dos e el ella ellas ellos en entre era eran es esa ese
    eso esta estan este esto estos fue fueron ha han hasta hay la las le les lo
    los mas me mi mis mucho muy nos o os para pero poco por porque pues que se
    sea segun ser si sin sobre solo son su sus tambien tanto te tiene tienen
    todo todos tu un una uno unos y ya""".split()
)

_TOKEN = re.compile(r"[a-z0-9]+")

# Sufijos del espanol, de mas largo a mas corto. NO es un stemmer serio: es lo
# minimo para que "lavado" y "lava" caigan en la misma dimension del mock. Solo
# afecta al modo de desarrollo — Gemini no pasa por aqui.
_SUFFIXES = (
    "aciones", "ciones", "cion", "mente", "iendo", "ando",
    "ados", "adas", "idos", "idas", "ado", "ada", "ido", "ida", "es", "s",
)


def _stem(token: str) -> str:
    for suffix in _SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            token = token[: -len(suffix)]
            break
    # Genero y vocal final: "banda"/"bandas" -> "band", "lavado"/"lava" -> "lav".
    if len(token) >= 4 and token[-1] in "aeo":
        token = token[:-1]
    return token


def tokenize(text: str) -> list[str]:
    """Minusculas, sin acentos, sin palabras vacias, con raiz aproximada.

    Se exporta porque el mock y las pruebas necesitan exactamente el mismo
    criterio de tokenizacion.
    """
    stripped = "".join(
        ch for ch in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(ch) != "Mn"
    )
    return [
        _stem(t) for t in _TOKEN.findall(stripped)
        if t not in _STOPWORDS and len(t) > 2
    ]


# --------------------------------------------------------------------- mock


class MockEmbedder:
    """Bolsa de palabras con hashing determinista (hashing trick).

    Cada token cae en una dimension fija segun su hash. El mismo texto produce
    siempre el mismo vector, asi que las pruebas son reproducibles. La similitud
    resultante es lexica, no semantica: sirve para verificar el pipeline, no
    para la demo.

    El umbral es bajo (0.20) porque el solapamiento lexico entre una frase de
    cliente y un perfil curado rara vez supera 0.5, aun cuando el match es bueno.

    4096 dimensiones y no 256: con textos de ~20 tokens, pocas ranuras producen
    colisiones de hash suficientes para que dos textos SIN nada en comun
    superen el umbral. Es el falso positivo clasico del hashing trick, y aqui
    se manifestaba como recuperar perfiles para consultas fuera de dominio.
    El costo de subirlo es irrelevante: el corpus son decenas de fragmentos.

    LIMITE CONOCIDO, y es la razon por la que la demo NO usa el mock: al ser
    lexico, confunde homonimos. "cuanto CUESTA el equipo" comparte raiz con
    "CUESTA arrancar" (carga de alta inercia) y recupera el perfil equivocado.
    Solo el embedder semantico distingue esos dos usos.
    """

    name = "mock"
    dim = 4096
    # Medidos sobre el corpus real (scripts/index_datasheets.py --stats): con
    # fragmentos de hoja de datos, las preguntas pertinentes caen en 0.15-0.19
    # y las ajenas en 0.00 exacto — no comparten ni una raiz. 0.10 separa con
    # margen amplio por ambos lados.
    default_min_score = 0.20
    long_text_min_score = 0.10

    def embed(self, texts: list[str], *, query: bool = False) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, text in enumerate(texts):
            for token in tokenize(text):
                slot = int(hashlib.blake2b(token.encode(), digest_size=4).hexdigest(), 16)
                out[i, slot % self.dim] += 1.0
        return _normalize(out)


# ------------------------------------------------------------------- gemini


class GeminiEmbedder:
    """gemini-embedding-001 via SDK google-genai.

    Umbral 0.55: con este modelo los pares relacionados caen tipicamente en
    0.6-0.85 y los no relacionados en 0.3-0.5, asi que 0.55 separa bien sin
    dejar fuera coincidencias legitimas.
    """

    name = "gemini"
    default_min_score = 0.55
    # Sobre fragmentos largos el coseno baja aunque el contenido sea el
    # correcto: el documento cubre mas temas que la pregunta.
    long_text_min_score = 0.45

    # Gemini acepta hasta 100 textos por peticion.
    _BATCH = 100

    def __init__(self, api_key: str, model: str = "gemini-embedding-001", dim: int = 768):
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY vacio. Ponlo en .env o usa EMBEDDING_PROVIDER=mock."
            )
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model
        self.dim = dim

    def embed(self, texts: list[str], *, query: bool = False) -> np.ndarray:
        from google.genai import types

        # Consulta y documento se proyectan distinto; usar el mismo task_type
        # para ambos degrada el recall de forma notable.
        task = "RETRIEVAL_QUERY" if query else "RETRIEVAL_DOCUMENT"

        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._BATCH):
            response = self._client.models.embed_content(
                model=self._model,
                contents=texts[start:start + self._BATCH],
                config=types.EmbedContentConfig(
                    task_type=task,
                    output_dimensionality=self.dim,
                ),
            )
            vectors.extend(e.values for e in response.embeddings)

        # Al truncar la dimension (output_dimensionality < 3072) Gemini deja de
        # devolver vectores normalizados. Normalizamos siempre nosotros.
        return _normalize(np.array(vectors, dtype=np.float32))


# ------------------------------------------------------------------ factory


def get_embedder(name: str | None = None) -> Embedder:
    """Devuelve el embedder activo.

    Por defecto sigue a `llm_provider`: si la demo corre con Gemini, el
    retrieval tambien. `EMBEDDING_PROVIDER` en .env permite desacoplarlos.
    """
    from app.config import settings

    provider = (name or settings.embedding_provider or settings.llm_provider).lower()

    if provider == "mock":
        return MockEmbedder()

    if provider == "gemini":
        return GeminiEmbedder(
            api_key=settings.gemini_api_key,
            model=settings.gemini_embedding_model,
            dim=settings.embedding_dim,
        )

    raise ValueError(
        f"Proveedor de embeddings desconocido: '{provider}'. Usa 'mock' o 'gemini'."
    )
