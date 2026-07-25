"""Loop de agente con tool calling.

Orquestacion: recibe la necesidad del cliente -> el modelo decide que
herramienta usar -> se ejecuta -> el resultado vuelve al modelo -> repite hasta
que produce una respuesta final o se agota `max_agent_steps`.

El loop es nuestro (no el del SDK) porque cada paso se traza. Esa traza es la
evidencia de arquitectura.
"""
from __future__ import annotations

from app.agent import tools as _tools  # noqa: F401  (registra las herramientas)
from app.agent.memory import Session, memory
from app.agent.registry import registry
from app.agent.tools import set_session
from app.agent.tracing import tracer
from app.config import settings
from app.llm.base import LLMProvider, Message
from app.llm.factory import get_provider
from app.state import state

SYSTEM_PROMPT = """\
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
- Si devuelve status SIN_SOLUCION: no te disculpes vagamente. Explica con
  precision cual restriccion hizo imposible el problema (viene en
  'nucleo_insatisfacible') y que haria falta para resolverlo (viene en
  'relajaciones', incluyendo el minimo viable). Es informacion valiosa, no un
  fracaso.
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


def _system_prompt(session: Session) -> str:
    return SYSTEM_PROMPT.format(brand=settings.brand, session_context=session.summary())


def run_agent(
    message: str,
    session_id: str = "default",
    provider: LLMProvider | None = None,
) -> dict:
    """Ejecuta un turno completo de conversacion.

    Devuelve la respuesta final, la traza de decisiones y el objetivo de
    negocio vigente en el momento de responder.
    """
    llm = provider or get_provider()
    session = memory.get(session_id)
    set_session(session_id)
    tracer.start(session_id)

    session.add(Message(role="user", content=message))
    schemas = registry.schemas()

    final_text = ""

    for step in range(settings.max_agent_steps):
        response = llm.complete(
            system=_system_prompt(session),
            messages=session.history,
            tools=schemas,
        )

        tracer.record(
            session_id, "llm",
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
            result = registry.execute(call.name, call.arguments)

            tracer.record(
                session_id, "tool",
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
        "trace": tracer.get(session_id),
        "known_requirements": session.known,
    }
