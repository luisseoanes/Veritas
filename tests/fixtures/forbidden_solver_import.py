"""Fixture de violación DELIBERADA - NO es código de producción.

Este archivo simula lo que NUNCA debe pasar: un módulo del núcleo simbólico
(como si viviera en app/solver/) que se acopla a la capa del LLM. Existe solo
para que el test de arquitectura demuestre que atrapa la infracción.

NUNCA se importa ni se ejecuta: vive fuera de app/, y el guard lo lee como
texto (AST), no lo corre. Si algún día este import se volviera real dentro de
app/solver/, el test `test_solver_layer_isolation` se pondría rojo.
"""
from app.llm.factory import get_provider  # noqa: F401  <-- LA violación a detectar


def elegir_configuracion(necesidad):
    # El pecado capital del proyecto: dejar que el modelo decida la config.
    provider = get_provider()
    return provider.complete(system="elige tú", messages=[], tools=[])
