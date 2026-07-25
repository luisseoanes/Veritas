"""Estado compartido de la aplicacion.

El grafo se construye una sola vez al arrancar. El objetivo de negocio activo
es mutable: el administrador lo cambia en vivo desde su panel y el agente lo
respeta en la siguiente consulta — ese es el momento clave de la demo.
"""
from __future__ import annotations

from app.data.catalog import load_graph
from app.graph.store import KnowledgeGraph
from app.solver.pareto import BUSINESS_OBJECTIVES, BusinessObjective


class AppState:
    def __init__(self) -> None:
        self.graph: KnowledgeGraph = load_graph()
        self._objective_key: str = "balanced"
        self._retrieval = None

    @property
    def objective(self) -> BusinessObjective:
        return BUSINESS_OBJECTIVES[self._objective_key]

    @property
    def objective_key(self) -> str:
        return self._objective_key

    def set_objective(self, key: str) -> BusinessObjective:
        if key not in BUSINESS_OBJECTIVES:
            raise ValueError(
                f"Objetivo desconocido '{key}'. Disponibles: {list(BUSINESS_OBJECTIVES)}"
            )
        self._objective_key = key
        return self.objective

    def reload_graph(self) -> KnowledgeGraph:
        """Recarga el catalogo (util al cambiar los datos sin reiniciar)."""
        self.graph = load_graph()
        return self.graph

    # ------------------------------------------------------------- retrieval

    @property
    def retrieval(self):
        """Indices vectoriales (RAG). Perezoso a proposito.

        El solver y el grafo no dependen del retrieval: `/solve` y el smoke test
        del motor no deben pagar el arranque de Chroma. Se construye la primera
        vez que una tool de recuperacion lo pide, o al arrancar la API.
        """
        if self._retrieval is None:
            from app.config import settings
            from app.retrieval.embedder import get_embedder
            from app.retrieval.index import Retrieval

            self._retrieval = Retrieval(settings.chroma_path, get_embedder())
            self._retrieval.bootstrap_profiles()
        return self._retrieval


state = AppState()
