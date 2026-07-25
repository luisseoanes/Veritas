"""Analitica nativa del grafo.

Aqui vive lo que una base vectorial NO puede producir: identificar que
componente sostiene estructuralmente el catalogo. Un embedding sabe que dos
productos "se parecen"; solo un grafo sabe que si un contactor se agota, el
40% de las configuraciones vendibles deja de existir.
"""
from __future__ import annotations

import networkx as nx

from app.graph.schema import Component, Kind
from app.graph.store import KnowledgeGraph


def betweenness_bottlenecks(graph: KnowledgeGraph, top_n: int = 5) -> list[dict]:
    """Componentes con mayor centralidad de intermediacion.

    Mide cuantos caminos de compatibilidad pasan por cada nodo. Alto valor =
    el componente es puente entre partes del catalogo que de otro modo no se
    conectarian.
    """
    scores = nx.betweenness_centrality(graph.nx)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    return [
        {
            "component_id": cid,
            "name": graph.get(cid).name,
            "kind": graph.get(cid).kind.value,
            "betweenness": round(score, 4),
            "stock": graph.get(cid).stock,
        }
        for cid, score in ranked
        if score > 0
    ]


def sole_option_bottlenecks(graph: KnowledgeGraph) -> list[dict]:
    """Componentes que son la UNICA opcion compatible para otros.

    Metrica mas accionable que la centralidad pura: si el componente X es el
    unico variador compatible con 12 motores del catalogo, agotarlo deja esos
    12 motores sin solucion vendible. Eso es un riesgo de inventario
    cuantificado, no una intuicion.
    """
    dependents: dict[str, list[str]] = {}

    for component in graph.all():
        for kind in Kind:
            if kind is component.kind:
                continue
            options = graph.compatible_with(component.id, kind)
            if len(options) == 1:
                only = options[0]
                dependents.setdefault(only.id, []).append(component.id)

    results = []
    for cid, deps in dependents.items():
        c = graph.get(cid)
        results.append({
            "component_id": cid,
            "name": c.name,
            "kind": c.kind.value,
            "stock": c.stock,
            "sole_option_for": len(deps),
            "dependents": sorted(deps),
        })
    return sorted(results, key=lambda r: r["sole_option_for"], reverse=True)


def articulation_points(graph: KnowledgeGraph) -> list[dict]:
    """Nodos de articulacion: su remocion parte el grafo en componentes aislados.

    En terminos de negocio: sin este producto, hay familias del catalogo que
    quedan sin ninguna ruta de compatibilidad hacia el resto.
    """
    points = list(nx.articulation_points(graph.nx))
    return [
        {
            "component_id": cid,
            "name": graph.get(cid).name,
            "kind": graph.get(cid).kind.value,
            "stock": graph.get(cid).stock,
        }
        for cid in points
    ]


def coverage_by_kind(graph: KnowledgeGraph, component_id: str) -> dict[str, int]:
    """Cuantas opciones compatibles tiene un componente, por tipo.

    Un motor con 0 variadores compatibles es un producto invendible como parte
    de una solucion — y eso es una senal de negocio, no un bug.
    """
    return {
        kind.value: len(graph.compatible_with(component_id, kind))
        for kind in Kind
        if kind is not graph.get(component_id).kind
    }


def orphans(graph: KnowledgeGraph) -> list[Component]:
    """Componentes sin ninguna arista: no participan en ninguna solucion valida."""
    return [c for c in graph.all() if graph.nx.degree(c.id) == 0]
