"""Herramientas del agente comercial.

Aqui esta la frontera entre el modelo y la verdad. El LLM traduce lenguaje
natural a los ARGUMENTOS de estas funciones — nada mas. La configuracion la
decide el solver, los numeros los calcula el codigo, la evidencia sale del
grafo. Si el modelo alucina, alucina argumentos, y el solver lo rechaza.

Las herramientas se dividen en tres grupos, y el orden importa:

  DECIDEN     solve_configuration        <- la unica que produce recomendaciones
  EXPLICAN    explain_configuration, check_compatibility, search_catalog
  PREPARAN    suggest_requirements, cite_datasheet   (capa RAG)

Las de RAG no deciden ni pueden: `suggest_requirements` devuelve restricciones
para que el cliente confirme y el solver valide, y `cite_datasheet` devuelve
texto citable. Ninguna de las dos puede armar una configuracion.
"""
from __future__ import annotations

import contextvars
import json

from app.agent.quotes import quotes
from app.agent.registry import registry
from app.config import settings
from app.graph.schema import Kind, SOLUTION_SLOTS
from app.intelligence.events import Event, EventType, event_log
from app.solver.engine import explain, solve
from app.solver.pareto import (
    frontier_payload,
    pareto_frontier,
    select_on_frontier,
)
from app.solver.requirements import (
    AttributeRequirement,
    BudgetRequirement,
    FeatureRequirement,
    Requirement,
    StockRequirement,
)
from app.state import state

# Sesion en curso, AISLADA POR REQUEST.
#
# Antes esto era un dict global mutable. El problema: run_agent() hace varias
# llamadas de red al LLM entre set_session() y el momento en que una tool lee el
# id (dentro de event_log.record). Con dos /chat concurrentes, el segundo pisaba
# el id del primero y los eventos quedaban mal atribuidos — envenenando el
# dashboard, que es la evidencia de negocio.
#
# Un ContextVar se copia por tarea/hilo: FastAPI corre cada request en su propio
# contexto (tambien los endpoints sincronos, via el threadpool de anyio), asi que
# cada request ve su propio id sin tener que pasarlo a mano por toda la cadena de
# tools. Fuera de un request, queda el default "default".
_current_session: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_session", default="default"
)


def set_session(session_id: str) -> None:
    _current_session.set(session_id)


def _session() -> "Session":
    """Sesion en curso. La memoria vive por sesion y el id ya esta aislado por
    request (ver `_current_session`)."""
    from app.agent.memory import memory

    return memory.get(_current_session.get())


# Hechos del cliente que se COMPLETAN desde memoria si el modelo no los repite.
#
# Solo datos duros del sitio y del proyecto: la potencia de la carga, el voltaje
# de la acometida y el presupuesto no cambian de un turno a otro, y si el modelo
# se olvida de repetirlos el solver resolveria OTRO problema sin que nadie lo
# note.
#
# `features` queda deliberadamente FUERA: es justo lo que el cliente retira
# ("quita el IP66"). Rellenarla desde memoria resucitaria una restriccion que
# acaba de descartar — un fallo peor que el que esto arregla.
REMEMBERED_FIELDS = ("power_kw", "voltage", "budget_cop")


def _build_requirements(
    power_kw: float | None,
    voltage: int | None,
    budget_cop: int | None,
    features: list[str] | None,
    require_stock: bool,
) -> list[Requirement]:
    """Traduce los argumentos del agente a restricciones nombradas."""
    reqs: list[Requirement] = []
    if power_kw is not None:
        reqs.append(AttributeRequirement(
            Kind.MOTOR, "power_kw", ">=", power_kw,
            f"El motor debe entregar al menos {power_kw:g} kW",
        ))
    if voltage is not None:
        reqs.append(AttributeRequirement(
            Kind.MOTOR, "voltage", "==", voltage,
            f"La red disponible es de {voltage} V",
        ))
    for feature in features or []:
        reqs.append(FeatureRequirement(feature))
    if require_stock:
        reqs.append(StockRequirement(1))
    if budget_cop is not None:
        reqs.append(BudgetRequirement(int(budget_cop)))
    return reqs


@registry.tool(
    name="solve_configuration",
    description=(
        "Resuelve una configuracion completa de accionamiento (motor, variador, "
        "proteccion y cable) que satisfaga los requerimientos del cliente. "
        "Devuelve la recomendacion principal y alternativas de la frontera de "
        "Pareto. Si NO existe solucion, devuelve el nucleo insatisfacible: las "
        "restricciones exactas que hacen imposible el problema, y el minimo "
        "viable. USA SIEMPRE esta herramienta antes de recomendar productos: "
        "nunca propongas una configuracion por tu cuenta."
    ),
    parameters={
        "type": "object",
        "properties": {
            "power_kw": {"type": "number", "description": "Potencia minima requerida en kW"},
            "voltage": {"type": "integer", "description": "Voltaje de la red disponible (220 o 440)"},
            "budget_cop": {"type": "integer", "description": "Presupuesto maximo total en pesos colombianos"},
            "features": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Caracteristicas exigidas: soft_start, modbus, profibus, pid, ip66",
            },
            "require_stock": {
                "type": "boolean",
                "description": "Exigir disponibilidad inmediata en inventario (por defecto true)",
            },
        },
        "required": [],
    },
)
def solve_configuration(
    power_kw: float | None = None,
    voltage: int | None = None,
    budget_cop: int | None = None,
    features: list[str] | None = None,
    require_stock: bool = True,
) -> str:
    graph = state.graph
    objective = state.objective
    session = _session()

    # La memoria COMPLETA lo que el modelo no repitio (nunca lo sobreescribe:
    # un valor explicito de este turno siempre gana). Sin esto, que el agente
    # recuerde el voltaje dependia de que el LLM lo re-enviara en cada llamada.
    completado_de_memoria = {}
    valores = {"power_kw": power_kw, "voltage": voltage, "budget_cop": budget_cop}
    for campo in REMEMBERED_FIELDS:
        if valores[campo] is None and session.known.get(campo) is not None:
            valores[campo] = session.known[campo]
            completado_de_memoria[campo] = valores[campo]
    power_kw, voltage, budget_cop = (
        valores["power_kw"], valores["voltage"], valores["budget_cop"]
    )

    requirements = _build_requirements(power_kw, voltage, budget_cop, features, require_stock)

    if not requirements:
        return json.dumps({
            "error": "Sin requerimientos. Pregunta al cliente potencia, voltaje y presupuesto.",
        }, ensure_ascii=False)

    result = solve(graph, requirements)
    req_summary = {
        "power_kw": power_kw, "voltage": voltage, "budget_cop": budget_cop,
        "features": features or [], "require_stock": require_stock,
    }

    # ------------------------------------------------------------ SIN SOLUCION
    if not result.satisfiable:
        minimum = next(
            (r["minimum_viable_cop"] for r in result.relaxations if "minimum_viable_cop" in r),
            None,
        )
        event_log.record(Event(
            type=EventType.UNMET,
            session_id=_current_session.get(),
            requirements=req_summary,
            unsat_core=[r.name for r in result.unsat_core],
            minimum_viable_cop=minimum,
            business_objective=state.objective_key,
        ))
        return json.dumps({
            "status": "SIN_SOLUCION",
            "explicacion": (
                "No existe ninguna configuracion valida. Las restricciones listadas "
                "en 'nucleo_insatisfacible' son, juntas, imposibles de cumplir. "
                "Es un nucleo MINIMO: quitar cualquiera de ellas vuelve el problema resoluble."
            ),
            "nucleo_insatisfacible": [
                {"restriccion": r.name, "descripcion": r.description} for r in result.unsat_core
            ],
            "relajaciones": result.relaxations,
            # Cada relajacion viable trae una configuracion REAL y cotizable.
            # Es lo que convierte el "no" en una oferta que el cliente puede
            # aceptar en el mismo turno.
            "alternativas_aceptables": [
                {
                    "si_cede_en": r["requirement"],
                    "que_significa": r["description"],
                    "te_puedo_ofrecer": r["proposal"]["components"],
                    "precio_total_cop": r["proposal"]["total_price_cop"],
                    "componentes": r["proposal"]["configuration"],
                    "disponibilidad_minima": r["proposal"]["min_stock"],
                }
                for r in result.relaxations
                if "proposal" in r
            ],
            "instruccion": (
                "Presenta las 'alternativas_aceptables' como ofertas concretas, "
                "con su precio exacto: 'si puedes ceder en X, te ofrezco esto por "
                "$Y'. Si el cliente ACEPTA una, llama a generate_quote con esos "
                "componentes. No inventes configuraciones distintas a estas."
            ),
            "configuraciones_evaluadas": result.considered,
        }, ensure_ascii=False, default=str)

    # ------------------------------------------------------------ CON SOLUCION
    frontier = pareto_frontier(result.solutions)

    # Lo que el cliente ya rechazo no se le vuelve a ofrecer. Aqui es donde la
    # memoria deja de ser un resumen en el prompt y cambia la recomendacion.
    # Si TODO lo que queda esta descartado se conserva la frontera completa: es
    # preferible repetir una opcion que quedarse sin nada que responder.
    descartadas = set(session.discarded)
    vigentes = [c for c in frontier if tuple(c.ids) not in descartadas]
    frontier_efectiva = vigentes or frontier

    chosen, ranking = select_on_frontier(frontier_efectiva, objective)

    event_log.record(Event(
        type=EventType.SOLVED,
        session_id=_current_session.get(),
        requirements=req_summary,
        configuration=list(chosen.ids),
        considered=sorted({cid for c in result.solutions for cid in c.ids}),
        total_price_cop=chosen.total_price_cop,
        total_margin_cop=chosen.total_margin_cop,
        business_objective=state.objective_key,
    ))

    alternatives = [
        {
            "componentes": entry["ids"],
            "precio_total_cop": entry["objectives"]["cost"],
            "eficiencia_motor_pct": entry["objectives"]["efficiency"],
            "disponibilidad": entry["objectives"]["availability"],
        }
        for entry in ranking[1:4]
    ]

    return json.dumps({
        "status": "RESUELTO",
        "recomendacion": {
            "componentes": {
                kind.value: {"id": c.id, "nombre": c.name, "precio_cop": c.price_cop}
                for kind, c in chosen.components.items()
            },
            "precio_total_cop": chosen.total_price_cop,
            "disponibilidad_minima": chosen.min_stock,
        },
        "alternativas_pareto": alternatives,
        "soluciones_factibles": result.count,
        "soluciones_en_frontera_pareto": len(frontier),
        # Trazabilidad de la memoria: que se completo sin que el cliente lo
        # repitiera, y cuantas opciones se excluyeron por rechazo previo.
        "completado_desde_memoria": completado_de_memoria or None,
        "descartadas_por_el_cliente": len(frontier) - len(frontier_efectiva),
        "objetivo_de_negocio_activo": {
            "clave": state.objective_key,
            "etiqueta": objective.label,
            "nota": (
                "El objetivo de negocio solo elige un punto DENTRO de la frontera de "
                "Pareto. Nunca puede recomendar una solucion dominada."
            ),
        },
    }, ensure_ascii=False, default=str)


@registry.tool(
    name="explain_configuration",
    description=(
        "Devuelve el rastro de evidencia de una configuracion: cada par de "
        "componentes, las reglas tecnicas que los gobiernan y si las cumplen. "
        "Usala cuando el cliente pregunte POR QUE una recomendacion es valida."
    ),
    parameters={
        "type": "object",
        "properties": {
            "component_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "IDs de los componentes de la configuracion",
            }
        },
        "required": ["component_ids"],
    },
)
def explain_configuration(component_ids: list[str]) -> str:
    from app.graph.schema import Configuration

    graph = state.graph
    components = {}
    for cid in component_ids:
        component = graph.get(cid)
        components[component.kind] = component

    return json.dumps(
        explain(graph, Configuration(components=components)),
        ensure_ascii=False, default=str,
    )


@registry.tool(
    name="check_compatibility",
    description=(
        "Verifica si dos componentes concretos son compatibles y devuelve las "
        "reglas tecnicas evaluadas con su resultado."
    ),
    parameters={
        "type": "object",
        "properties": {
            "component_a": {"type": "string"},
            "component_b": {"type": "string"},
        },
        "required": ["component_a", "component_b"],
    },
)
def check_compatibility(component_a: str, component_b: str) -> str:
    return json.dumps(
        state.graph.evidence(component_a, component_b),
        ensure_ascii=False, default=str,
    )


@registry.tool(
    name="search_catalog",
    description=(
        "Lista componentes del catalogo filtrando por tipo. Util para responder "
        "que hay disponible antes de resolver una configuracion completa."
    ),
    parameters={
        "type": "object",
        "properties": {
            "kind": {
                "type": "string",
                "enum": ["motor", "drive", "protection", "cable"],
                "description": "Tipo de componente",
            },
            "voltage": {"type": "integer", "description": "Filtrar por voltaje operativo"},
        },
        "required": ["kind"],
    },
)
def search_catalog(kind: str, voltage: int | None = None) -> str:
    components = state.graph.of_kind(Kind(kind))
    if voltage is not None:
        components = [c for c in components if c.accepts_voltage(voltage)]

    return json.dumps({
        "cantidad": len(components),
        "componentes": [
            {
                "id": c.id, "nombre": c.name, "precio_cop": c.price_cop,
                "stock": c.stock, **{k: v for k, v in c.attrs.items() if k != "tags"},
            }
            for c in components
        ],
    }, ensure_ascii=False, default=str)


@registry.tool(
    name="discard_configuration",
    description=(
        "Registra que el cliente RECHAZO una configuracion concreta, para no "
        "volver a ofrecersela. Usala cuando diga que no le sirve, que no le "
        "gusta, que ya la tiene o que quiere ver otra cosa. "
        "Despues vuelve a llamar a solve_configuration: la siguiente "
        "recomendacion evitara automaticamente lo descartado."
    ),
    parameters={
        "type": "object",
        "properties": {
            "component_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "IDs de la configuracion que el cliente rechazo",
            },
            "reason": {
                "type": "string",
                "description": "Por que la rechazo, en palabras del cliente (opcional)",
            },
        },
        "required": ["component_ids"],
    },
)
def discard_configuration(component_ids: list[str], reason: str = "") -> str:
    """Anota el rechazo en la memoria de la sesion.

    No es un registro decorativo: `solve_configuration` excluye lo descartado
    de la frontera antes de elegir, asi que esto cambia de verdad la siguiente
    recomendacion.
    """
    session = _session()
    graph = state.graph

    # Se normaliza al orden canonico de la configuracion para que el descarte
    # coincida aunque el modelo liste los ids en otro orden.
    try:
        ordered = tuple(
            sorted(component_ids, key=lambda cid: SOLUTION_SLOTS.index(graph.get(cid).kind))
        )
    except KeyError as exc:
        return json.dumps({"error": f"Componente inexistente: {exc}"}, ensure_ascii=False)

    session.discard(ordered)

    return json.dumps({
        "status": "DESCARTADA",
        "configuracion": list(ordered),
        "motivo": reason or "no indicado",
        "total_descartadas": len(session.discarded),
        "instruccion": (
            "Confirma brevemente que no volveras a proponerla y vuelve a llamar "
            "a solve_configuration para ofrecer la siguiente mejor opcion."
        ),
    }, ensure_ascii=False, default=str)


@registry.tool(
    name="compare_products",
    description=(
        "Compara dos o mas productos del catalogo lado a lado: precio, "
        "especificaciones tecnicas y en que se diferencian exactamente. "
        "Usala cuando el cliente pregunte en que se diferencian dos productos, "
        "cual le conviene, o para que tipo de usuario es cada uno. "
        "Solo compara: NO elige por el cliente ni arma configuraciones."
    ),
    parameters={
        "type": "object",
        "properties": {
            "component_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "IDs de los productos a comparar (2 o mas)",
            }
        },
        "required": ["component_ids"],
    },
)
def compare_products(component_ids: list[str]) -> str:
    """Comparativa lado a lado, con las diferencias ya calculadas.

    El LLM no tiene que deducir en que se diferencian: el codigo determina que
    atributos difieren y cuales coinciden. Asi la respuesta no depende de que
    el modelo compare bien dos listas de numeros.
    """
    graph = state.graph
    if len(component_ids) < 2:
        return json.dumps({
            "error": "Se necesitan al menos 2 productos para comparar.",
        }, ensure_ascii=False)

    components = [graph.get(cid) for cid in component_ids]

    kinds = {c.kind for c in components}
    # Atributos numericos/textuales presentes en alguno de los productos.
    attr_names = sorted({k for c in components for k in c.attrs if k != "tags"})

    diferencias, comunes = {}, {}
    for name in attr_names:
        values = {c.id: c.attrs.get(name) for c in components}
        distinct = {json.dumps(v, sort_keys=True, default=str) for v in values.values()}
        (diferencias if len(distinct) > 1 else comunes)[name] = values

    precios = {c.id: c.price_cop for c in components}
    barato = min(precios, key=precios.get)
    caro = max(precios, key=precios.get)

    return json.dumps({
        "comparables": len(kinds) == 1,
        "nota_de_comparabilidad": (
            "Todos son del mismo tipo, la comparacion es directa."
            if len(kinds) == 1 else
            "OJO: son de tipos distintos; cumplen funciones diferentes dentro de "
            "la solucion y no son sustitutos entre si. Dilo antes de compararlos."
        ),
        "productos": [
            {
                "id": c.id, "nombre": c.name, "tipo": c.kind.value,
                "precio_cop": c.price_cop, "stock": c.stock,
                "caracteristicas": sorted(c.features),
                "atributos": {k: v for k, v in c.attrs.items() if k != "tags"},
            }
            for c in components
        ],
        "en_que_se_diferencian": diferencias,
        "en_que_coinciden": comunes,
        "diferencia_de_precio_cop": precios[caro] - precios[barato],
        "mas_economico": barato,
        "mas_costoso": caro,
        "instruccion": (
            "Explica las diferencias que importan para el uso del cliente, no "
            "todas. Los numeros son exactos: reportalos tal cual. Si el cliente "
            "pregunta cual le conviene, apoyate en las diferencias pero recuerda "
            "que la configuracion final la decide solve_configuration."
        ),
    }, ensure_ascii=False, default=str)


@registry.tool(
    name="generate_quote",
    description=(
        "ACCION REAL: emite una cotizacion formal para una configuracion que el "
        "cliente ya ACEPTO, con numero consecutivo, desglose por componente y "
        "validez. Devuelve el numero de cotizacion y la deja registrada. "
        "Usala SOLO cuando el cliente haya aceptado explicitamente una "
        "configuracion concreta — no para mostrarle opciones."
    ),
    parameters={
        "type": "object",
        "properties": {
            "component_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "IDs de los componentes aceptados por el cliente",
            },
            "customer_name": {
                "type": "string",
                "description": "Nombre del cliente o de su empresa, si lo dijo",
            },
            "notes": {
                "type": "string",
                "description": "Observaciones a dejar en la cotizacion (opcional)",
            },
        },
        "required": ["component_ids"],
    },
)
def generate_quote(
    component_ids: list[str],
    customer_name: str = "Cliente",
    notes: str = "",
) -> str:
    """Emite la cotizacion y la persiste.

    Es la unica tool que CAMBIA algo fuera del proceso: escribe un documento y
    consume un consecutivo. Por eso valida antes de emitir — una cotizacion de
    una configuracion invalida seria un compromiso comercial sobre algo que no
    se puede entregar.
    """
    from app.graph.schema import Configuration

    graph = state.graph
    components = {}
    for cid in component_ids:
        component = graph.get(cid)
        components[component.kind] = component

    config = Configuration(components=components)

    # GUARDRAIL: no se cotiza lo que el grafo no aprueba.
    evidence = explain(graph, config)
    if not evidence["all_rules_pass"]:
        return json.dumps({
            "status": "RECHAZADA",
            "motivo": (
                "La combinacion no cumple las reglas tecnicas del grafo, asi que "
                "no se emite cotizacion. Vuelve a resolver con solve_configuration."
            ),
            "evidencia": evidence["checks"],
        }, ensure_ascii=False, default=str)

    sin_stock = [c.id for c in components.values() if c.stock < 1]

    quote = quotes.issue(
        config=config,
        customer_name=customer_name,
        notes=notes,
        objective_key=state.objective_key,
        session_id=_current_session.get(),
    )

    return json.dumps({
        "status": "EMITIDA",
        "numero": quote["numero"],
        "cliente": quote["cliente"],
        "emitida": quote["emitida"],
        "valida_hasta": quote["valida_hasta"],
        "items": quote["items"],
        "total_cop": quote["total_cop"],
        "advertencia_stock": (
            f"Sin inventario inmediato: {sin_stock}. Confirmar plazo de entrega."
            if sin_stock else None
        ),
        "archivo": quote["archivo"],
        "instruccion": (
            "Confirmale al cliente el NUMERO de cotizacion, el total y hasta "
            "cuando es valida. Los importes son los del documento emitido: no "
            "los recalcules ni los redondees."
        ),
    }, ensure_ascii=False, default=str)


# ===========================================================================
# CAPA RAG — prepara y respalda. Nunca decide.
# ===========================================================================


@registry.tool(
    name="suggest_requirements",
    description=(
        "Traduce la descripcion de la APLICACION del cliente (que va a mover, en "
        "que ambiente trabaja, con que urgencia) a restricciones tecnicas "
        "CANDIDATAS. Usala cuando el cliente describe su problema en sus propias "
        "palabras pero no da especificaciones. "
        "NO devuelve productos ni configuraciones: devuelve sugerencias que "
        "debes CONFIRMAR con el cliente antes de usarlas. Solo lo que el cliente "
        "confirme se pasa a solve_configuration. "
        "No infiere potencia ni voltaje: esos siempre se preguntan."
    ),
    parameters={
        "type": "object",
        "properties": {
            "application": {
                "type": "string",
                "description": (
                    "Descripcion de la aplicacion en las palabras del cliente. "
                    "Pasala lo mas literal posible: no la traduzcas a jerga tecnica."
                ),
            }
        },
        "required": ["application"],
    },
)
def suggest_requirements(application: str) -> str:
    from app.retrieval import profiles as profile_corpus

    hits = state.retrieval.profiles.search(application, k=settings.retrieval_top_k)

    if not hits:
        return json.dumps({
            "status": "SIN_COINCIDENCIAS",
            "instruccion": (
                "No hay un perfil de aplicacion que coincida. No inventes "
                "restricciones: preguntale al cliente directamente por potencia, "
                "voltaje, ambiente de trabajo y urgencia."
            ),
        }, ensure_ascii=False)

    merged, conflicts = profile_corpus.combine(
        [chunk.meta.get("suggests", {}) for chunk, _ in hits]
    )

    return json.dumps({
        "status": "SUGERENCIAS_SIN_CONFIRMAR",
        "instruccion": (
            "Estas son HIPOTESIS derivadas de como el cliente describio su "
            "aplicacion, no requerimientos. Presentaselas como preguntas "
            "('entiendo que hay lavado a presion, te confirmo IP66?') citando el "
            "motivo. Solo lo que el cliente confirme entra a solve_configuration. "
            "Nunca las apliques por tu cuenta ni las presentes como decididas."
        ),
        "sugerencias": [
            {
                "perfil": chunk.meta.get("key"),
                "restricciones": chunk.meta.get("suggests"),
                "porque": chunk.meta.get("rationale"),
                "confianza": round(score, 3),
            }
            for chunk, score in hits
        ],
        "combinado_si_el_cliente_confirma_todo": merged,
        "conflictos": conflicts,
        "faltante_obligatorio": [
            "power_kw: depende de la carga real, no se infiere de la aplicacion",
            "voltage: depende de la acometida del sitio (220 o 440)",
        ],
    }, ensure_ascii=False, default=str)


@registry.tool(
    name="cite_datasheet",
    description=(
        "Busca en las hojas de datos oficiales de WEG el respaldo documental de "
        "una pregunta tecnica (instalacion, derating, condiciones de operacion, "
        "normas, garantia) y devuelve los fragmentos literales con su documento "
        "y numero de pagina. "
        "NO recomienda ni elige productos, y NO es fuente de precios ni de "
        "especificaciones: para eso estan search_catalog y solve_configuration. "
        "Si no devuelve respaldo, dilo: no completes con conocimiento propio."
    ),
    parameters={
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "Pregunta tecnica concreta del cliente",
            },
            "component_id": {
                "type": "string",
                "description": "Opcional: acotar la busqueda a un producto concreto",
            },
        },
        "required": ["question"],
    },
)
def cite_datasheet(question: str, component_id: str | None = None) -> str:
    index = state.retrieval.datasheets

    if index.count() == 0:
        return json.dumps({
            "status": "SIN_CORPUS",
            "instruccion": (
                "No hay hojas de datos indexadas en este despliegue. Dile al "
                "cliente que no puedes respaldarlo documentalmente y ofrece "
                "responder con datos del catalogo (search_catalog), que si son "
                "exactos. No inventes citas ni numeros de pagina."
            ),
        }, ensure_ascii=False)

    hits = index.search(question, k=settings.retrieval_top_k)

    if component_id:
        # Se prefiere lo que menciona el componente, pero no se descarta el
        # resto: una nota general de instalacion sigue siendo respaldo valido.
        focused = [(c, s) for c, s in hits if component_id in c.component_ids]
        hits = focused or hits

    if not hits:
        return json.dumps({
            "status": "SIN_RESPALDO",
            "instruccion": (
                "La documentacion indexada no responde esto. Dilo explicitamente "
                "('no tengo respaldo documental para eso') en vez de afirmar. "
                "Puedes ofrecer consultarlo con soporte tecnico."
            ),
        }, ensure_ascii=False)

    return json.dumps({
        "status": "CON_RESPALDO",
        "instruccion": (
            "Cita de forma fiel y menciona documento y pagina. No extrapoles mas "
            "alla de lo que dice el texto, y no tomes de aqui precios ni "
            "especificaciones numericas."
        ),
        "fragmentos": [
            {
                "texto": chunk.text,
                "documento": chunk.source,
                "pagina": chunk.page,
                "componentes_mencionados": chunk.component_ids,
                "similitud": round(score, 3),
            }
            for chunk, score in hits
        ],
    }, ensure_ascii=False, default=str)
