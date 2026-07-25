# Dos chatbots sobre un solo motor — cliente y administrador

> **Origen:** lo pide el equipo de ML/DS — un endpoint de chat para el cliente y otro para el
> administrador. Este doc es el spec de **arquitectura y backend** para implementarlo.
>
> **Frontera de responsabilidad (importante):**
> - **ML/DS (ellos):** el *comportamiento conversacional* del chatbot admin — el system prompt
>   (persona), qué debe saber hacer, cómo se redactan las descripciones de las tools, y cualquier
>   diferencia de RAG. Eso es diseño de conducta del modelo.
> - **Backend (tú):** todo el *plumbing* — endpoints, parametrización del loop, filtrado de tools,
>   auth, namespacing de memoria y los *wrappers* de las tools de admin (que solo llaman a código
>   que ya existe). Nada de esto es ML.

## 1. Qué es cada chatbot

| | Chatbot **cliente** (ya existe) | Chatbot **admin** (nuevo) |
|---|---|---|
| Endpoint | `POST /chat` (abierto) | `POST /admin/chat` (token) |
| Persona | Asesor comercial técnico | Analista de inteligencia de negocio |
| Para qué | Traducir la necesidad del cliente → configuración vía solver | Consultar la BI en lenguaje natural (oportunidades, cuellos de botella, frontera, objetivo activo) **y cambiar el objetivo de negocio** |
| Tools | Las 6 actuales (solve, explain, check, search, suggest, cite) | Lectura de BI + **una de escritura** (`set_business_objective`), ver §5. **No** tiene `solve_configuration` |
| Escribe eventos | Sí (SOLVED/UNMET → alimentan los detectores) | **No** (no debe contaminar el log de mercado) |

El chatbot admin es *BI conversacional* sobre lo que el dashboard ya muestra: *"¿qué producto me
falta y para cuántos clientes?"*, *"¿qué restricción bloquea más ventas?"*, *"muéstrame la frontera
para 5 kW a 440 V"*. Buen ángulo de **Innovación** para el jurado: **dos agentes, un motor**.

## 2. La decisión de arquitectura clave

**Un solo loop parametrizado, NO dos agentes.** La guía del evento advierte contra construir varios
agentes cuando uno bien parametrizado basta. `run_agent` no cambia de lógica: solo recibe un
**perfil** que decide tres cosas — *system prompt*, *conjunto de tools* y *namespace de sesión*.

Todo lo demás (el loop de tool-calling, la traza, la memoria, los guardrails) se reutiliza igual.

## 3. Cambios de código concretos

### 3.1 Un `AgentProfile` (nuevo, en `app/agent/loop.py` o `app/agent/profiles.py`)

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class AgentProfile:
    key: str                       # "cliente" | "admin"  -> también namespacea la sesión
    system_prompt: str             # plantilla con {brand} y {session_context}
    tool_names: tuple[str, ...]    # subconjunto del registry que este agente puede usar

CLIENTE = AgentProfile(
    key="cliente",
    system_prompt=CLIENT_SYSTEM_PROMPT,   # el SYSTEM_PROMPT actual, renombrado
    tool_names=("solve_configuration", "explain_configuration",
                "check_compatibility", "search_catalog",
                "suggest_requirements", "cite_datasheet"),
)

ADMIN = AgentProfile(
    key="admin",
    system_prompt=ADMIN_SYSTEM_PROMPT,    # <- lo redacta ML/DS (persona analista)
    tool_names=("get_opportunities", "get_bottlenecks", "get_frontier",
                "get_active_objective", "set_business_objective"),  # ver §5
)
```

### 3.2 `run_agent` parametrizado (`app/agent/loop.py`)

Firma actual: `run_agent(message, session_id="default", provider=None)`. Nueva:

```python
def run_agent(message, session_id="default", *, profile=CLIENTE, provider=None) -> dict:
    llm = provider or get_provider()
    sid = f"{profile.key}:{session_id}"      # namespacing -> memoria/traza/eventos aislados
    session = memory.get(sid)
    set_session(sid)
    tracer.start(sid)
    ...
    schemas = registry.schemas(only=list(profile.tool_names))   # ya soportado por el registry
    system = profile.system_prompt.format(brand=settings.brand,
                                          session_context=session.summary())
    ...
```

Dos detalles:
- **Namespacing de sesión** (`f"{profile.key}:{session_id}"`): garantiza que una sesión `admin`
  y una `cliente` con el mismo `session_id` **no compartan memoria ni traza**. Cero acoplamiento.
- **`registry.schemas(only=...)`** ya existe (`registry.py:35`). No hay que tocar el registry.

### 3.3 Endurecer el filtro en el loop (guardrail)

Hoy `registry.execute(name, ...)` corre cualquier tool registrada. Al separar audiencias, el loop
debe **rechazar** una tool fuera del perfil (por si el modelo alucina un nombre):

```python
for call in response.tool_calls:
    if call.name not in profile.tool_names:
        result = f"ERROR: '{call.name}' no está disponible para este agente."
    else:
        result = registry.execute(call.name, call.arguments)
```

Así el chatbot cliente **no puede** tocar una tool de admin ni al revés, aunque el prompt falle.

### 3.4 Partir el system prompt

El `SYSTEM_PROMPT` actual pasa a llamarse `CLIENT_SYSTEM_PROMPT` (sin cambios). Se añade
`ADMIN_SYSTEM_PROMPT` **cuyo contenido lo escribe ML/DS**. Deja un stub con la persona:

```python
ADMIN_SYSTEM_PROMPT = """\
Eres un analista de inteligencia de negocio de {brand}. Respondes preguntas del ADMINISTRADOR
sobre el estado comercial usando SOLO las herramientas: oportunidades, cuellos de botella,
frontera y objetivo activo. NUNCA inventes cifras — cada número viene de una herramienta y trae
su fórmula. No recomiendas productos a clientes: eso es del asesor comercial.
{session_context}
"""
```

## 4. Los dos endpoints (`app/main.py`)

```python
@app.post("/chat", tags=["cliente"])
def chat(request: ChatRequest) -> dict:
    return run_agent(request.message, session_id=request.session_id, profile=CLIENTE)

@app.post("/admin/chat", tags=["admin"], dependencies=[Depends(require_admin)])
def admin_chat(request: ChatRequest) -> dict:
    return run_agent(request.message, session_id=request.session_id, profile=ADMIN)
```

`ChatRequest` se reutiliza tal cual. `/admin/chat` queda protegido por `require_admin` (ya existe).

## 5. Tools de admin (wrappers, `app/agent/admin_tools.py` nuevo)

**Cero lógica nueva: cada una envuelve código que ya existe.** Se registran en el mismo `registry`.

| Tool | Envuelve | Devuelve |
|---|---|---|
| `get_opportunities` | `detect_all(event_log, state.graph)` (`intelligence/detectors.py`) | Detectores con su `formula` visible |
| `get_bottlenecks` | `sole_option_bottlenecks(state.graph)` (`graph/queries.py`) | Componentes que son única opción compatible |
| `get_frontier` | `solve()` + `pareto_frontier()` (igual que `/admin/frontier`) | Frontera + dominadas + elegido por objetivo |
| `get_active_objective` | `state.objective` / `BUSINESS_OBJECTIVES` | Objetivo activo y presets disponibles |
| `set_business_objective` | `state.set_objective(key)` — **escritura** | Cambia el objetivo activo. Efecto **global**: altera lo que recomienda el asesor del cliente |

**Ninguna de las de lectura registra eventos**, y `set_business_objective` tampoco → el chatbot
admin no contamina el log de mercado (los detectores siguen midiendo solo conversaciones reales de
clientes). Esto sale gratis por no darle `solve_configuration` al perfil admin.

> ✅ **DECIDIDO (ML/DS, 2026-07-25): con escritura.** El chatbot admin **puede cambiar el objetivo
> de negocio** vía `set_business_objective`. Condiciones obligatorias:
> - Solo acepta uno de los **4 presets** — `state.set_objective()` ya valida y revienta con un valor
>   desconocido, así que el modelo no puede inventar una política.
> - El `ADMIN_SYSTEM_PROMPT` debe instruir a **confirmar antes de aplicar** (*"¿confirmo que cambie
>   a maximizar margen?"*) — nunca flipear ante una pregunta hipotética (*"¿y si liberara stock?"*).
> - Es la **única** acción con efecto del chatbot; todo lo demás es lectura.
>
> ⚠️ **Nota de backend:** el objetivo es **estado global compartido** — cambiarlo desde el chat
> admin afecta de inmediato al asesor del cliente (es lo buscado: el "momento de la demo"). Aun así,
> para el momento *clave* del pitch, el botón determinista `POST /admin/objective` es más seguro que
> depender de que el modelo interprete bien; usa el chat-write como demostración adicional, no como
> el mecanismo del que depende la demo.

## 6. Guardrails que se conservan (no se relajan)

- **El LLM sigue sin decidir números.** El admin lee BI vía tools; cada cifra trae su `formula` o
  sale del solver. La regla innegociable #1 se mantiene.
- **El test de arquitectura (B11) no se rompe.** Las tools de admin viven en `app/agent/` e
  importan `intelligence/`, `graph/`, `solver/` — permitido. El núcleo (`graph/`, `solver/`) sigue
  sin importar nada del agente.
- **Auth:** `/admin/chat` bajo `require_admin`; `/chat` abierto. Igual que el resto de `/admin/*`.
- **La única acción con efecto (cambiar objetivo) es un cambio de *política*, no de configuración.**
  No viola la regla #2 (el LLM no arma configuraciones): elige entre 4 presets validados por
  `state.set_objective()`, con confirmación conversacional. Sigue siendo el solver quien decide qué
  configuración se recomienda *dentro* de ese objetivo.

## 7. Tests a añadir (`tests/test_admin_chat.py`)

- `POST /admin/chat` sin token → **401**; con token → **200**.
- `POST /chat` sigue abierto (sin token → 200).
- El perfil `ADMIN.tool_names` **no** incluye `solve_configuration`; el `CLIENTE` **no** incluye
  las tools de admin (verificable sin LLM, comparando conjuntos).
- (mock) una vuelta de `/admin/chat` **no** crea eventos `SOLVED/UNMET` en el `event_log`.
- `set_business_objective` con un preset válido cambia `state.objective_key`; con un valor
  desconocido lanza `ValueError` y **no** cambia el estado (validación de `state.set_objective`).

## 8. Impacto en el frontend (`docs/02-frontend-guia.md`)

El dashboard de admin suma un **widget de chat** que pega a `POST /admin/chat` con el header
`X-Admin-Token`. El chat del cliente sigue en `POST /chat`. Mismo formato de request/response que
`/chat`. Conviene anotarlo en el contrato cuando esto se implemente.

## 9. Plan por fases (pequeño, seguro para la demo)

1. **C1** — `AgentProfile` + `run_agent(profile=...)` + endurecer el filtro de tools. El perfil
   `CLIENTE` reproduce el comportamiento actual **sin cambios** (regresión: la suite sigue verde).
   ✅ **HECHO (2026-07-25):** ver §11.
2. **C2** — partir el system prompt (`CLIENT_` + `ADMIN_` stub para ML/DS).
3. **C3** — `admin_tools.py` (los 4 wrappers de lectura).
4. **C4** — endpoint `POST /admin/chat` con perfil `ADMIN`.
5. **C5** — tests (`tests/test_admin_chat.py`).
6. **C6** — ML/DS redacta `ADMIN_SYSTEM_PROMPT` y ajusta descripciones de tools.

C1–C5 son tuyos (backend) y no dependen de ML/DS. C6 es de ellos y puede ir en paralelo.

## 11. Estado de implementación

- [x] **C1** · `AgentProfile` + `run_agent(profile=...)` + guardrail de tools — ✅ *hecho
  (2026-07-25):* los **35 tests siguen verdes** (regresión pura, cero cambios de contrato para el
  cliente). Detalles de implementación:
  - `AgentProfile` (frozen dataclass) y el perfil `CLIENTE` viven en `app/agent/loop.py` (el doc
    permitía `loop.py` o `profiles.py`; se dejó en `loop.py` para C1 sin churn — `CLIENTE` reutiliza
    el `SYSTEM_PROMPT` actual tal cual, C2 partirá los prompts).
  - `run_agent(message, session_id="default", *, profile=CLIENTE, provider=None)`. `profile` es
    **keyword-only** → las llamadas posicionales existentes no se rompen.
  - **Namespacing** `sid = f"{profile.key}:{session_id}"` aplicado a memoria, `set_session`, traza
    y `tracer.get`. El campo `session_id` de la respuesta sigue siendo el **crudo** (contrato del
    front intacto).
  - **Guardrail** en el loop: una tool fuera de `profile.tool_names` devuelve `ERROR: '<name>' no
    esta disponible para este agente.` en vez de ejecutarse.
  - **`GET /trace/{session_id}`** ahora resuelve bajo el namespace `cliente:` → sigue devolviendo
    la traza del cliente igual que antes, y de paso **no expone** trazas del futuro chatbot admin.
  - `POST /chat` pasa `profile=CLIENTE` explícito.
- [ ] **C2** · partir el system prompt (`CLIENT_SYSTEM_PROMPT` + `ADMIN_SYSTEM_PROMPT` stub).
- [ ] **C3** · `admin_tools.py` (4 wrappers de lectura).
- [ ] **C4** · endpoint `POST /admin/chat` (perfil `ADMIN`). ← *al cerrar esta, actualizar §8 y
  `docs/02-frontend-guia.md` con el contrato del widget de chat admin.*
- [ ] **C5** · `tests/test_admin_chat.py` (§7).
- [ ] **C6** · ML/DS: `ADMIN_SYSTEM_PROMPT` + descripciones de tools.

## 10. Decisiones de ML/DS (2026-07-25) — resueltas

1. **Qué hace el chatbot admin:** BI conversacional (lectura) **+ cambiar el objetivo de negocio**
   (escritura). Ver §5.
2. **¿Solo lectura o con efectos de lado?** → **Con efectos de lado** (escritura habilitada), con
   las condiciones de §5: solo presets válidos y confirmación antes de aplicar.
3. **¿Admin fuera del `event_log` de cliente?** → **Sí.** Se logra no dándole `solve_configuration`
   (única tool que registra eventos).
4. **¿Comparten algo las dos personas?** → **No.** Memoria y sesión namespaceadas por perfil.
