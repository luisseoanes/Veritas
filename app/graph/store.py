"""El grafo de conocimiento.

Nodos = componentes reales del catalogo.
Aristas = compatibilidad tecnica DERIVADA de `app/graph/rules.py`.

Ninguna arista se escribe a mano. Esa es la diferencia entre un grafo de
conocimiento y una lista de productos con relaciones inventadas: aqui cada
arista es trazable a una regla de ingenieria concreta.
"""
from __future__ import annotations

import networkx as nx

from app.graph.rules import COMPATIBILITY_RULES, is_compatible, rules_for
from app.graph.schema import Component, Kind

EDGE_COMPATIBLE = "COMPATIBLE_WITH"


class KnowledgeGraph:
    def __init__(self) -> None:
        self._g = nx.Graph()
        self._components: dict[str, Component] = {}
        self._built = False

    # ------------------------------------------------------------------ carga

    def add(self, component: Component) -> None:
        if component.id in self._components:
            raise ValueError(f"Componente duplicado: {component.id}")
        self._components[component.id] = component
        self._g.add_node(component.id, kind=component.kind.value, component=component)
        self._built = False

    def add_many(self, components: list[Component]) -> None:
        for c in components:
            self.add(c)

    def build(self) -> "KnowledgeGraph":
        """Deriva todas las aristas de compatibilidad aplicando las reglas.

        O(n^2) sobre el catalogo. Con cientos de componentes es instantaneo, y
        se recalcula solo cuando el catalogo cambia.
        """
        self._g.remove_edges_from(list(self._g.edges))
        items = list(self._components.values())

        for i, a in enumerate(items):
            for b in items[i + 1:]:
                if a.kind is b.kind:
                    continue  # Dos motores no se "conectan" entre si.
                applicable = rules_for(a, b)
                if not applicable:
                    continue  # Sin regla en comun: no modelamos la relacion.
                if is_compatible(a, b):
                    self._g.add_edge(
                        a.id, b.id,
                        type=EDGE_COMPATIBLE,
                        rules=[r.name for r in applicable],
                    )
        self._built = True
        return self

    # --------------------------------------------------------------- consulta

    def __len__(self) -> int:
        return len(self._components)

    @property
    def edge_count(self) -> int:
        return self._g.number_of_edges()

    @property
    def nx(self) -> nx.Graph:
        """Acceso al grafo crudo (para algoritmos de centralidad)."""
        return self._g

    def get(self, component_id: str) -> Component:
        try:
            return self._components[component_id]
        except KeyError:
            raise KeyError(f"No existe el componente '{component_id}'") from None

    def all(self) -> list[Component]:
        return list(self._components.values())

    def of_kind(self, kind: Kind) -> list[Component]:
        return [c for c in self._components.values() if c.kind is kind]

    def compatible_with(self, component_id: str, kind: Kind | None = None) -> list[Component]:
        """Vecinos compatibles, opcionalmente filtrados por tipo.

        Este es el recorrido que fundamenta cada recomendacion: el agente nunca
        propone un componente que no salga de aqui.
        """
        self._require_built()
        neighbors = (self._components[n] for n in self._g.neighbors(component_id))
        if kind is None:
            return list(neighbors)
        return [c for c in neighbors if c.kind is kind]

    def are_compatible(self, a_id: str, b_id: str) -> bool:
        """True si existe arista derivada de compatibilidad entre ambos."""
        self._require_built()
        return self._g.has_edge(a_id, b_id)

    def pair_allowed(self, a_id: str, b_id: str) -> bool:
        """True si el par puede coexistir en una solucion.

        Distinto de `are_compatible`: cuando ningun regla gobierna el par (por
        ejemplo cable y proteccion, que no se restringen mutuamente) no hay
        arista, pero tampoco hay prohibicion. Ausencia de restriccion no es
        incompatibilidad.
        """
        self._require_built()
        a, b = self.get(a_id), self.get(b_id)
        if not rules_for(a, b):
            return True
        return self._g.has_edge(a_id, b_id)

    def evidence(self, a_id: str, b_id: str) -> dict:
        """Por que estos dos componentes son (o no) compatibles.

        Devuelve las reglas evaluadas y su resultado. Es lo que se muestra en la
        demo para probar que la respuesta esta fundamentada y no alucinada.
        """
        a, b = self.get(a_id), self.get(b_id)
        applicable = rules_for(a, b)
        return {
            "a": a.id,
            "b": b.id,
            "compatible": is_compatible(a, b),
            "rules_evaluated": [
                {
                    "name": r.name,
                    "description": r.description,
                    "passes": r.holds(a, b),
                }
                for r in applicable
            ],
        }

    def stats(self) -> dict:
        return {
            "components": len(self._components),
            "edges": self._g.number_of_edges(),
            "by_kind": {k.value: len(self.of_kind(k)) for k in Kind},
            "rules": len(COMPATIBILITY_RULES),
            "built": self._built,
        }

    def _require_built(self) -> None:
        if not self._built:
            raise RuntimeError(
                "El grafo no ha sido construido. Llama a .build() despues de cargar componentes."
            )
