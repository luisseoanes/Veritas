"""Loop de agente con tool calling.

Orquestacion: recibe la necesidad del cliente -> el modelo decide que
herramienta usar -> se ejecuta -> el resultado vuelve al modelo -> repite hasta
que produce una respuesta final o se agota `max_agent_steps`.

El loop es nuestro (no el del SDK) porque cada paso se traza. Esa traza es la
evidencia de arquitectura.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.agent import admin_tools as _admin_tools  # noqa: F401  (registra tools admin)
from app.agent import tools as _tools  # noqa: F401  (registra las herramientas)
from app.agent.memory import Session, memory
from app.agent.registry import registry
from app.agent.tools import set_session
from app.agent.tracing import tracer
from app.config import settings
from app.llm.base import LLMProvider, Message
from app.llm.factory import get_provider
from app.state import state

CLIENT_SYSTEM_PROMPT = """\
Eres un asesor comercial tecnico de {brand}, especializado en accionamientos
industriales (motores, variadores de frecuencia, proteccion y cableado).

REGLA ABSOLUTA — no la rompas nunca:
NUNCA propongas, inventes ni combines productos por tu cuenta. Toda
recomendacion debe salir de la herramienta `solve_configuration`. Tu trabajo es
traducir lo que el cliente dice a los argumentos de esa herramienta, y despues
explicar en lenguaje natural lo que ella devolvio. Los numeros que reportes
deben ser exactamente los que la herramienta entrego: no los estimes, no los
redondees, no los inventes.

Como conversar:
- Si el cliente describe su APLICACION en sus palabras ("una banda en la zona
  de lavado") pero no da especificaciones, llama primero a
  `suggest_requirements`. Lo que devuelve son HIPOTESIS: presentaselas como
  preguntas con su motivo, y usa solo lo que el cliente confirme. Nunca las
  des por decididas.
- Si falta informacion esencial (potencia en kW, voltaje de red, presupuesto),
  preguntala. Haz UNA sola pregunta por turno, la que mas reduzca la
  incertidumbre. Potencia y voltaje jamas se deducen: se preguntan.
- Cuando tengas lo suficiente, llama a `solve_configuration`.
- Si la herramienta devuelve status RESUELTO: presenta la recomendacion con su
  precio total, y menciona brevemente que existen alternativas en la frontera
  de Pareto si el cliente quiere otro balance costo/desempeno.
- Si devuelve status SIN_SOLUCION: NO vuelvas a llamar a `solve_configuration`
  quitando restricciones por tu cuenta. Un "no hay solucion" no es un error que
  debas esquivar: es el hallazgo mas valioso que produce el sistema, y
  esquivarlo en silencio se lo oculta al cliente. Responde en este orden:
    1. Di exactamente que restriccion lo hizo imposible ('nucleo_insatisfacible'),
       y que es un nucleo MINIMO: quitar cualquiera lo vuelve resoluble.
    2. Si el nucleo NO incluye el presupuesto, es una BRECHA DE CATALOGO: no
       existe producto para ese perfil a NINGUN precio. Dilo con esas palabras
       — es informacion comercial, no una disculpa.
    3. Si el nucleo incluye el presupuesto, es una BRECHA DE PRECIO: di el
       minimo viable real y cuanto falta (vienen en 'relajaciones').
    4. Si el nucleo incluye la disponibilidad (stock), el problema no es
       tecnico: el producto existe pero no hay inventario. Ofrece cotizarlo con
       plazo de entrega en vez de cerrar la venta.
    5. Si la restriccion culpable salio de una sugerencia que el cliente NUNCA
       confirmo (por ejemplo IP66 propuesto por la aplicacion), acláralo y
       PREGUNTALE si puede ceder en ella. Solo si el cliente responde que si,
       vuelve a llamar a la herramienta sin esa restriccion.
    6. Y SIEMPRE cierra con las 'alternativas_aceptables': son configuraciones
       reales, con precio exacto, que existirian si cediera en cada punto.
       Presentalas como oferta concreta ("si puedes subir a $X, te entrego
       esto"), no como teoria. Un "no" sin alternativa es una venta perdida.

- Si el cliente ACEPTA una configuracion —la recomendada o una alternativa—,
  llama a `generate_quote` con esos componentes y dale el numero de cotizacion.
  No la emitas antes de que acepte, y nunca inventes un numero: sale de la
  herramienta.
- Si pregunta en que se diferencian dos productos, cual le conviene o para que
  tipo de usuario es cada uno, usa `compare_products`. No compares de memoria.
- Si RECHAZA una recomendacion ("esa no me sirve", "muestrame otra"), llama a
  `discard_configuration` con esos componentes y vuelve a resolver. No repitas
  una opcion que ya rechazo.
- No vuelvas a preguntar datos que el cliente YA dio: la herramienta los
  recuerda. Si en su respuesta aparece 'completado_desde_memoria', significa
  que se reutilizo lo que ya habia dicho; no lo presentes como un supuesto tuyo
  ni se lo vuelvas a preguntar.
- Si el cliente pregunta por que una configuracion es valida, usa
  `explain_configuration` y cita las reglas tecnicas concretas.
- Para preguntas de instalacion, condiciones de operacion, normas o garantia,
  usa `cite_datasheet` y cita documento y pagina. Si devuelve SIN_RESPALDO o
  SIN_CORPUS, dilo tal cual: "no tengo respaldo documental para eso". Nunca
  completes ese vacio con conocimiento propio ni inventes una pagina.

Jerarquia de fuentes — respetala siempre:
1. Precios, potencias, corrientes y stock: SOLO de `solve_configuration` o
   `search_catalog`. Nunca de un texto recuperado.
2. Compatibilidad tecnica: SOLO del grafo (`explain_configuration`,
   `check_compatibility`).
3. Prosa tecnica (instalacion, normas): de `cite_datasheet`, citando la fuente.

Responde en espanol, con precision tecnica y sin relleno comercial.

Contexto de la sesion:
{session_context}
"""


# STUB — lo redacta ML/DS en C6 (persona + descripciones finales de tools).
# Backend deja aqui la persona minima y las CONDICIONES DURAS que el prompt debe
# respetar (ver docs/03 §5): no inventar cifras y confirmar antes de escribir el
# objetivo. No amplies el alcance mas alla de esto sin coordinar con ML/DS.
ADMIN_SYSTEM_PROMPT = """\
Eres un analista de inteligencia de negocio de {brand}. Respondes preguntas del
ADMINISTRADOR sobre el estado comercial usando SOLO las herramientas
disponibles: oportunidades, cuellos de botella, frontera de Pareto y objetivo
de negocio activo.

REGLA ABSOLUTA — no la rompas nunca:
NUNCA inventes cifras. Cada numero que reportes viene de una herramienta y trae
su formula o su origen en el solver; si no tienes la tool para responder algo,
dilo. No recomiendas productos a clientes: eso es del asesor comercial.

Sobre cambiar el objetivo de negocio (`set_business_objective`) — unica accion
con efecto:
- Solo existen 4 presets validos; la herramienta rechaza cualquier otro valor.
- CONFIRMA SIEMPRE antes de aplicar ("¿confirmo que cambie a maximizar
  margen?"). Nunca cambies el objetivo ante una pregunta hipotetica
  ("¿y si liberara stock?") — eso es analisis, no una orden.
- Es un cambio de POLITICA global: afecta de inmediato lo que el asesor
  recomienda a los clientes. Adviertelo al confirmar.

Responde en espanol, con precision analitica y sin relleno.

Contexto de la sesion:
{session_context}
"""


@dataclass(frozen=True)
class AgentProfile:
    """Perfil que parametriza `run_agent`: un solo loop, distintas audiencias.

    Decide tres cosas y nada mas — persona (`system_prompt`), herramientas
    permitidas (`tool_names`) y namespace de sesion (`key`). Todo el resto del
    loop (traza, memoria, guardrails) se reutiliza igual. Ver docs/03.
    """

    key: str                       # "cliente" | "admin" -> namespacea la sesion
    system_prompt: str             # plantilla con {brand} y {session_context}
    tool_names: tuple[str, ...]    # subconjunto del registry que este agente usa


# Perfil del asesor comercial (el chatbot que ya existia). Usa el prompt del
# cliente, sin cambios respecto al comportamiento historico.
CLIENTE = AgentProfile(
    key="cliente",
    system_prompt=CLIENT_SYSTEM_PROMPT,
    tool_names=(
        "solve_configuration", "explain_configuration",
        "check_compatibility", "search_catalog", "compare_products",
        "suggest_requirements", "cite_datasheet",
        # Memoria con efecto: lo descartado deja de ofrecerse en el proximo solve.
        "discard_configuration",
        # Unica tool que EJECUTA una accion (emite y persiste un documento).
        # Solo el perfil de cliente la tiene: es el cierre de su venta.
        "generate_quote",
    ),
)


# Perfil del analista de negocio (chatbot admin). BI de lectura + una unica tool
# de escritura (set_business_objective). NO incluye `solve_configuration` -> por
# eso nunca registra eventos en el log de mercado. Ver docs/03 §5.
ADMIN = AgentProfile(
    key="admin",
    system_prompt=ADMIN_SYSTEM_PROMPT,
    tool_names=(
        "get_opportunities", "get_bottlenecks", "get_frontier",
        "get_active_objective", "set_business_objective",
        # Contrafactual: cuantifica el retorno de cerrar una brecha, volviendo a
        # resolver las ventas perdidas reales. Solo lee: no toca el catalogo.
        "simulate_product",
    ),
)


def _system_prompt(profile: AgentProfile, session: Session) -> str:
    return profile.system_prompt.format(
        brand=settings.brand, session_context=session.summary()
    )


def run_agent(
    message: str,
    session_id: str = "default",
    *,
    profile: AgentProfile = CLIENTE,
    provider: LLMProvider | None = None,
) -> dict:
    """Ejecuta un turno completo de conversacion bajo un `profile`.

    Devuelve la respuesta final, la traza de decisiones y el objetivo de
    negocio vigente en el momento de responder. El perfil `CLIENTE` reproduce
    el comportamiento historico sin cambios.
    """
    llm = provider or get_provider()
    # Namespacing por perfil: una sesion `admin` y una `cliente` con el mismo
    # session_id NO comparten memoria/traza/eventos. Cero acoplamiento.
    sid = f"{profile.key}:{session_id}"
    session = memory.get(sid)
    set_session(sid)
    tracer.start(sid)

    session.add(Message(role="user", content=message))
    schemas = registry.schemas(only=list(profile.tool_names))

    final_text = ""

    for step in range(settings.max_agent_steps):
        response = llm.complete(
            system=_system_prompt(profile, session),
            messages=session.history,
            tools=schemas,
        )

        tracer.record(
            sid, "llm",
            step=step + 1,
            provider=llm.name,
            text=response.text[:500],
            tool_calls=[{"name": c.name, "arguments": c.arguments} for c in response.tool_calls],
        )

        session.add(Message(
            role="assistant",
            content=response.text,
            tool_calls=response.tool_calls,
        ))

        if not response.wants_tools:
            final_text = response.text
            break

        for call in response.tool_calls:
            # Guardrail: rechaza cualquier tool fuera del perfil, aunque el
            # modelo alucine un nombre. El cliente no puede tocar tools de
            # admin ni al reves, incluso si el prompt falla.
            if call.name not in profile.tool_names:
                result = f"ERROR: '{call.name}' no esta disponible para este agente."
            else:
                result = registry.execute(call.name, call.arguments)

            tracer.record(
                sid, "tool",
                name=call.name,
                arguments=call.arguments,
                result=result[:2000],
            )

            # Los argumentos aceptados por el solver son hechos confirmados del
            # cliente: se acumulan en memoria para no volver a preguntarlos.
            if call.name == "solve_configuration":
                session.remember(**call.arguments)

            session.add(Message(
                role="tool",
                content=result,
                tool_call_id=call.id,
                tool_name=call.name,
            ))
    else:
        final_text = (
            "Alcance el limite de pasos sin cerrar la consulta. "
            "Reformula la necesidad con potencia, voltaje y presupuesto."
        )

    return {
        "session_id": session_id,
        "reply": final_text,
        "business_objective": state.objective_key,
        "trace": tracer.get(sid),
        "known_requirements": session.known,
    }
