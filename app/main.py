"""API de la plataforma.

Dos superficies sobre el mismo motor:
  /chat            -> interfaz de cliente (agente comercial)
  /admin/*         -> interfaz de administrador (inteligencia de negocio)

El momento clave de la demo vive en el cruce de ambas: el administrador cambia
el objetivo en POST /admin/objective y la siguiente consulta a /chat devuelve
una recomendacion distinta — sin salir de la frontera de Pareto.
"""
from __future__ import annotations

import logging
import secrets
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.agent.loop import run_agent
from app.agent.memory import memory
from app.agent.tracing import tracer
from app.config import settings
from app.llm.factory import get_provider
from app.graph.queries import sole_option_bottlenecks
from app.graph.schema import Kind
from app.intelligence.detectors import detect_all
from app.intelligence.events import EventType, event_log
from app.solver.engine import solve
from app.solver.pareto import (
    BUSINESS_OBJECTIVES,
    frontier_payload,
    pareto_frontier,
    select_on_frontier,
)
from app.solver.requirements import (
    AttributeRequirement,
    BudgetRequirement,
    FeatureRequirement,
    StockRequirement,
)
from app.state import state

def _validate_config() -> None:
    """Falla RUIDOSAMENTE al arrancar si la configuracion no sirve.

    Antes, un LLM en 'gemini' sin API key no fallaba hasta el primer /chat —en
    medio de la demo— y un ADMIN_TOKEN vacio dejaba el panel sin proteger. Se
    prefiere que el proceso no levante a descubrirlo en vivo (regla innegociable
    #3: cero mock silencioso en el camino critico).
    """
    # Construir el provider ya: si es 'gemini' sin key, revienta aqui, no en el
    # primer mensaje. Con 'mock' no exige nada.
    get_provider()
    # El embedder puede seguir a otro proveedor que el LLM (config.py); valida
    # su caso aparte.
    effective_embed = (settings.embedding_provider or settings.llm_provider).lower()
    if effective_embed == "gemini" and not settings.gemini_api_key:
        raise RuntimeError(
            "EMBEDDING en gemini sin GEMINI_API_KEY. Corrige .env o usa mock."
        )
    if not settings.admin_token:
        raise RuntimeError(
            "ADMIN_TOKEN vacio: el panel de admin quedaria sin proteger. Genera "
            'uno (python -c "import secrets; print(secrets.token_urlsafe(24))") y '
            "ponlo en .env."
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Arranque de la app en un solo lugar (reemplaza los @app.on_event).

    1) Valida la configuracion (fail-fast).
    2) Recupera el historico en disco para que el dashboard arranque con datos.
    3) Deja los indices vectoriales listos: con Gemini, indexar los perfiles es
       una llamada de red que no queremos pagar en medio de la demo. Idempotente.
    """
    _validate_config()
    event_log.load_from_disk()
    state.retrieval.bootstrap_profiles()
    yield


app = FastAPI(
    title="Plataforma de Inteligencia Comercial Neuro-Simbolica",
    description=(
        "Agente comercial sobre grafo de conocimiento + solver de restricciones. "
        "No busca productos: resuelve un problema de configuracion."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

logger = logging.getLogger("reshapex")


# ------------------------------------------------------------ manejo de errores
#
# Toda respuesta de error sale con el MISMO envelope: {"error": {...}}. Sin esto,
# una excepcion no capturada devolvia un 500 con stacktrace crudo — feo y ademas
# una fuga de detalles internos si pasa delante del jurado.


def _error(status_code: int, message: str, **extra) -> JSONResponse:
    body = {"error": {"status": status_code, "message": message, **extra}}
    return JSONResponse(status_code=status_code, content=body)


@app.exception_handler(StarletteHTTPException)
async def _handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """401/400/404 y demas HTTPException, con el envelope comun."""
    return _error(exc.status_code, str(exc.detail))


@app.exception_handler(RequestValidationError)
async def _handle_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
    """422 de Pydantic, resumido a campo -> mensaje (JSON-serializable)."""
    detalles = [
        {"campo": ".".join(str(p) for p in err["loc"]), "error": err["msg"]}
        for err in exc.errors()
    ]
    return _error(422, "Datos de entrada invalidos.", detalles=detalles)


@app.exception_handler(Exception)
async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
    """Cualquier excepcion no prevista: se loguea entera del lado servidor, pero
    al cliente solo le llega un mensaje generico — nunca el stacktrace."""
    logger.exception("Error no manejado en %s %s", request.method, request.url.path)
    return _error(500, "Error interno del servidor.")


# --------------------------------------------------------------------- salud


@app.get("/health", tags=["sistema"])
def health() -> dict:
    return {
        "status": "ok",
        "brand": settings.brand,
        "llm_provider": settings.llm_provider,
        "graph": state.graph.stats(),
        "eventos_registrados": len(event_log),
        "objetivo_activo": state.objective_key,
    }


# ------------------------------------------------------------------- cliente


class ChatRequest(BaseModel):
    message: str = Field(..., description="Mensaje del cliente")
    session_id: str = Field("default", description="Identificador de la conversacion")


@app.post("/chat", tags=["cliente"])
def chat(request: ChatRequest) -> dict:
    """Un turno de conversacion con el asesor comercial."""
    return run_agent(request.message, session_id=request.session_id)


@app.get("/trace/{session_id}", tags=["cliente"])
def get_trace(session_id: str) -> dict:
    """Traza de decisiones: que herramienta llamo el agente, con que y que obtuvo.

    Es la evidencia de arquitectura que se muestra al jurado.
    """
    return {"session_id": session_id, "steps": tracer.get(session_id)}


class SolveRequest(BaseModel):
    # gt=0: potencia, voltaje y presupuesto negativos o cero no tienen sentido
    # fisico. Al ser Optional, la restriccion solo aplica si se envia un valor;
    # None sigue siendo valido (el requerimiento simplemente no se agrega).
    power_kw: float | None = Field(default=None, gt=0)
    voltage: int | None = Field(default=None, gt=0)
    budget_cop: int | None = Field(default=None, gt=0)
    features: list[str] = Field(default_factory=list)
    require_stock: bool = True


def _requirements_from(request: SolveRequest) -> list:
    """Traduce un SolveRequest a restricciones del solver.

    Compartido por /solve y /admin/frontier para que las dos rutas no diverjan:
    ambas resuelven exactamente el mismo problema a partir del mismo cuerpo.
    """
    requirements = []
    if request.power_kw is not None:
        requirements.append(AttributeRequirement(Kind.MOTOR, "power_kw", ">=", request.power_kw))
    if request.voltage is not None:
        requirements.append(AttributeRequirement(Kind.MOTOR, "voltage", "==", request.voltage))
    for feature in request.features:
        requirements.append(FeatureRequirement(feature))
    if request.require_stock:
        requirements.append(StockRequirement(1))
    if request.budget_cop is not None:
        requirements.append(BudgetRequirement(request.budget_cop))
    return requirements


@app.post("/solve", tags=["cliente"])
def solve_direct(request: SolveRequest) -> dict:
    """Acceso directo al solver, sin LLM de por medio.

    Existe para demostrar en vivo que la logica no depende del modelo: los
    mismos requerimientos producen el mismo resultado con o sin Gemini.
    """
    requirements = _requirements_from(request)
    if not requirements:
        raise HTTPException(400, "Envia al menos un requerimiento.")

    result = solve(state.graph, requirements)
    payload = result.to_dict()
    if result.satisfiable:
        payload["pareto_frontier"] = frontier_payload(pareto_frontier(result.solutions))
    return payload


# -------------------------------------------------------------------- admin


def require_admin(x_admin_token: str = Header(default="")) -> None:
    """Guard de las rutas de administrador. Token compartido, sin usuarios.

    El cliente (chat, /solve) es abierto; el administrador (cambiar el objetivo
    de negocio, resetear la demo) exige el header `X-Admin-Token`. Se compara con
    `secrets.compare_digest` para no filtrar informacion por timing.
    """
    if not settings.admin_token:
        # Fail-closed: sin token configurado en el servidor, nadie pasa. B5
        # convierte esto en un fallo de arranque para que no pase desapercibido.
        raise HTTPException(500, "El servidor no tiene ADMIN_TOKEN configurado.")
    if not secrets.compare_digest(x_admin_token, settings.admin_token):
        raise HTTPException(401, "Token de administrador invalido o ausente.")


@app.get("/admin/verify", tags=["admin"])
def verify_admin(_: None = Depends(require_admin)) -> dict:
    """Valida el token de admin. La pantalla de login del front la usa para
    comprobar el token antes de entrar al panel."""
    return {"ok": True}


@app.get("/admin/dashboard", tags=["admin"], dependencies=[Depends(require_admin)])
def dashboard() -> dict:
    """Inteligencia de negocio en tiempo real.

    Se recalcula en cada llamada sobre los eventos acumulados, asi que una
    conversacion nueva en /chat se refleja aqui de inmediato.
    """
    report = detect_all(event_log, state.graph)
    report["resumen"] = {
        "conversaciones_totales": len(event_log),
        "resueltas": len(event_log.of_type(EventType.SOLVED)),
        "sin_solucion": len(event_log.of_type(EventType.UNMET)),
        "objetivo_activo": state.objective_key,
    }
    return report


@app.get("/admin/objectives", tags=["admin"], dependencies=[Depends(require_admin)])
def list_objectives() -> dict:
    return {
        "activo": state.objective_key,
        "disponibles": [
            {"clave": key, "etiqueta": obj.label, "pesos": obj.weights}
            for key, obj in BUSINESS_OBJECTIVES.items()
        ],
        "garantia": (
            "Los objetivos solo eligen un punto DENTRO de la frontera de Pareto. "
            "Ninguna configuracion dominada es alcanzable, sea cual sea el objetivo."
        ),
    }


class ObjectiveRequest(BaseModel):
    key: str = Field(..., description="balanced | customer_value | maximize_margin | clear_inventory")


@app.post("/admin/objective", tags=["admin"], dependencies=[Depends(require_admin)])
def set_objective(request: ObjectiveRequest) -> dict:
    """Cambia el objetivo comercial activo. El agente lo respeta desde la
    siguiente consulta — este es el interruptor de la demo."""
    try:
        objective = state.set_objective(request.key)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"activo": state.objective_key, "etiqueta": objective.label, "pesos": objective.weights}


@app.post("/admin/frontier", tags=["admin"], dependencies=[Depends(require_admin)])
def admin_frontier(request: SolveRequest) -> dict:
    """La frontera de Pareto de un escenario, con el punto que elige cada objetivo.

    Recibe los mismos requerimientos que /solve (el escenario que se esta
    demostrando) y devuelve: la frontera, las soluciones dominadas (para pintarlas
    en gris) y, por cada objetivo de negocio, que punto de la frontera elegiria.
    Es el dato que mueve el grafico cuando el admin cambia el objetivo — sin sacar
    nunca al cliente de la frontera.
    """
    requirements = _requirements_from(request)
    if not requirements:
        raise HTTPException(400, "Envia al menos un requerimiento.")

    result = solve(state.graph, requirements)
    if not result.satisfiable:
        return {
            "status": "SIN_SOLUCION",
            "nucleo_insatisfacible": [r.name for r in result.unsat_core],
        }

    frontier = pareto_frontier(result.solutions)
    frontier_ids = {tuple(c.ids) for c in frontier}
    dominated = [c for c in result.solutions if tuple(c.ids) not in frontier_ids]

    chosen_by_objective = {}
    for key, objective in BUSINESS_OBJECTIVES.items():
        chosen, _ranking = select_on_frontier(frontier, objective)
        chosen_by_objective[key] = {
            "ids": list(chosen.ids),
            "precio_cop": chosen.total_price_cop,
        }

    return {
        "status": "OK",
        "frontera": frontier_payload(frontier),
        "dominadas": frontier_payload(dominated),
        "elegida_por_objetivo": chosen_by_objective,
    }


class ResetRequest(BaseModel):
    # Por defecto NO borra el historico: las ~400 sesiones alimentan el
    # dashboard y no queremos perderlas al reiniciar un ensayo.
    keep_history: bool = True


@app.post("/demo/reset", tags=["admin"], dependencies=[Depends(require_admin)])
def demo_reset(request: ResetRequest) -> dict:
    """Devuelve el sistema al estado inicial de la demo (entre ensayos).

    Limpia la memoria de conversacion y las trazas, recarga el grafo desde el
    catalogo y vuelve el objetivo activo a 'balanced'. Con keep_history=False
    ademas vacia el log de eventos (el historico del dashboard).
    """
    memory.reset_all()
    tracer.clear_all()
    state.reload_graph()
    state.set_objective("balanced")
    if not request.keep_history:
        event_log.clear()
    return {
        "status": "reset",
        "historico_conservado": request.keep_history,
        "objetivo_activo": state.objective_key,
        "eventos_registrados": len(event_log),
    }


@app.get("/admin/bottlenecks", tags=["admin"], dependencies=[Depends(require_admin)])
def bottlenecks() -> dict:
    """Cuellos de botella estructurales del catalogo (analitica del grafo)."""
    return {"cuellos_de_botella": sole_option_bottlenecks(state.graph)}


@app.get("/graph/stats", tags=["admin"])
def graph_stats() -> dict:
    return state.graph.stats()


# ---------------------------------------------------------------- retrieval


@app.get("/retrieval/stats", tags=["admin"])
def retrieval_stats() -> dict:
    """Estado de los indices vectoriales: con que embedder y cuanto hay dentro."""
    return state.retrieval.stats()


class SuggestRequest(BaseModel):
    application: str = Field(
        ...,
        description="Aplicacion descrita en las palabras del cliente",
        examples=["una banda transportadora en la zona de lavado de la planta"],
    )


@app.post("/retrieval/suggest", tags=["admin"])
def suggest(request: SuggestRequest) -> dict:
    """Traduccion aplicacion -> restricciones candidatas, sin LLM de por medio.

    Igual que /solve respecto del solver: demuestra que el puente semantico es
    codigo con un umbral, no una interpretacion del modelo. Lo que sale de aqui
    son restricciones sin confirmar, nunca productos.
    """
    from app.agent.tools import suggest_requirements
    import json as _json

    return _json.loads(suggest_requirements(request.application))


@app.get("/graph/evidence", tags=["admin"])
def graph_evidence(a: str, b: str) -> dict:
    """Por que dos componentes son o no compatibles, regla por regla."""
    try:
        return state.graph.evidence(a, b)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
