# Backend — flujo de trabajo y backlog ajustado

> Documento vivo del trabajo de backend previo al 25/07. Frontera de responsabilidad:
> `app/graph/`, `app/solver/`, `app/intelligence/detectors.py`, `catalog.py`, `rules.py`,
> `profiles.py` = dominio (no se toca aquí). Todo lo de abajo es infraestructura de API.
>
> Los specs de B2/B3/B5/B6 se **corrigieron contra el código** — el backlog original tenía
> tres imprecisiones (documentadas abajo). Cada B trae solución concreta lista para implementar.

## Orden de ataque

`B11 → B6 → B8 → B1 → B2 → B5 → B3 → B7 → B9 → B10 → ~~B4~~ → B13` · el frontend corre en paralelo
(ver [02-frontend-guia.md](02-frontend-guia.md)). B2 y B3 van **después** de B1 (necesitan el
guard de auth). **B4 se cerró como NO APLICA** (el front es Next.js con servidor propio + CORS, no
un estático a montar; ver estado abajo). **B13 ✅ hecho** ⇒ el backlog de backend queda cerrado.

## Estado (se marca aquí a medida que se completa)

- [x] **B11** · Test de arquitectura — ✅ *hecho:* `tests/test_architecture.py` (3 tests). Incluye un **test negativo** con violación plantada (`tests/fixtures/forbidden_solver_import.py`) que prueba que el guard *muerde*, no solo que pasa. `python -m tests.test_architecture` es una **demo de jurado** autocontenida. `requirements.txt` +pytest +httpx.
- [x] **B6** · Erradicar carrera de sesión — ✅ *hecho:* `_current_session` pasó de dict global a `contextvars.ContextVar` en `tools.py`. Regresión en `tests/test_session_isolation.py` (2 tests). Smoke test sigue verde.
- [x] **B8** · Validación de rangos en `SolveRequest` — ✅ *hecho:* `Field(gt=0)` en `power_kw`/`voltage`/`budget_cop`. Test `tests/test_solve_validation.py` (7 casos).
- [x] **B1** · Auth de admin + login — ✅ *hecho:* `require_admin` (header `X-Admin-Token`, `secrets.compare_digest`, fail-closed) en las 4 rutas `/admin/*`; `GET /admin/verify` como login del front; `admin_token` en `config.py` + `ADMIN_TOKEN` en `.env.example`. Test `tests/test_auth.py` (6). **Desbloquea B2 y B3.**
- [x] **B2** · `POST /admin/frontier` — ✅ *hecho:* recibe un `SolveRequest` y devuelve `frontera` + `dominadas` + `elegida_por_objetivo`. Helper `_requirements_from` compartido con `/solve`. Guardado por `require_admin`. Test `tests/test_frontier.py` (4), incluye el invariante "cada objetivo elige DENTRO de la frontera".
- [x] **B5** · Validación de proveedores en arranque — ✅ *hecho:* `_validate_config` (gemini sin key, embeddings sin key, `ADMIN_TOKEN` vacío → el proceso no levanta). De paso migré los 3 `@app.on_event` a un único `lifespan` — mueren los warnings de deprecación. Test `tests/test_startup_validation.py` (4).
- [x] **B3** · `POST /demo/reset` — ✅ *hecho:* añadidos `memory.reset_all()` y `tracer.clear_all()`; el endpoint limpia memoria/trazas, recarga el grafo, vuelve el objetivo a `balanced`, y con `keep_history=False` vacía el log. Guardado por `require_admin`. Test `tests/test_demo_reset.py` (5).
- [x] **B7** · Manejo global de errores — ✅ *hecho:* handlers para `Exception` (500 limpio, sin filtrar stacktrace, logueado del lado servidor), `HTTPException` y `RequestValidationError`, todos con envelope `{"error": {...}}`. Test `tests/test_error_handling.py` (4).
- [x] **B9** · Logging estructurado — ✅ *hecho (2026-07-25):* `app/observability.py` (nuevo) con
  `request_id` por request (ContextVar) inyectado en cada log vía filtro, formato greppable
  `clave=valor` y `configure_logging()` idempotente que cuelga de `reshapex` sin pisar uvicorn.
  Middleware HTTP en `main.py` loguea `method/path/status/latency_ms` + header `X-Request-ID`.
  `run_agent` loguea `agent_turn` con perfil, provider, pasos y **tools llamadas** — correlacionado
  por el mismo `request_id`.
- [x] **B10** · Tests de API con `TestClient` — ✅ *hecho (2026-07-25):* `tests/test_api.py` (5),
  complementa lo ya cubierto sin duplicar: `/health` + contrato, header `X-Request-ID` (B9),
  `/solve` válido, `/admin/*` sin token → 401, y la **carrera de B6 a través de `/chat` real**
  (8 conversaciones concurrentes; cada evento queda atribuido a su sesión namespaceada, cero
  cruces). El `event_log` se aísla por test en un archivo temporal.
- [~] **B4** · Servir el frontend (`StaticFiles`) — ❌ *NO APLICA (2026-07-25):* superado por la
  arquitectura del front. El front que llegó es una app **Next.js 15 (App Router)** en `frontend/`
  (no un bundle estático en `web/`), diseñada para correr como **servidor propio** (dev en `:3000`,
  deploy en **Vercel**) y pegarle a la API por HTTP vía `NEXT_PUBLIC_API_BASE_URL` + **CORS** (ya
  habilitado). `next.config.ts` no usa `output: 'export'`, así que no hay estático que montar. El
  objetivo real de B4 —que el front sea accesible— queda cubierto por CORS + Vercel. Ver
  `frontend/COMO-CORRER.md` y `docs/02` §"Cómo se sirve el front".
- [x] **B13** · `.env.example` + scripts de arranque — ✅ *hecho (2026-07-25):* `.env.example`
  completado con todas las variables de `config.py` (LLM, retrieval `EMBEDDING_PROVIDER`/
  `GEMINI_EMBEDDING_MODEL`/`EMBEDDING_DIM`/`CHROMA_PATH`/`RETRIEVAL_TOP_K`, `ADMIN_TOKEN`,
  `CORS_ORIGINS`). Scripts **`run.sh`** (Linux/macOS) y **`run.ps1`** (Windows), idempotentes: crean
  venv, instalan deps, copian `.env` desde el ejemplo la primera vez y levantan uvicorn. Smoke:
  `./run.sh` arranca la API (`/health` 200, header `X-Request-ID`). **Con esto el backlog de
  backend queda cerrado** (B4 no aplica).

> **Workstream paralelo — dual chatbot (C1–C6):** el chatbot admin sobre el mismo motor se
> rastrea en [03-chatbot-dual.md](03-chatbot-dual.md) §11. Es backend (C1–C5) + ML/DS (C6).
> **C1–C5 ✅ hechos (2026-07-25) — backend del dual chatbot COMPLETO:** `run_agent` parametrizado
> por `AgentProfile`, namespacing de sesión por perfil, guardrail de tools (C1); split del system
> prompt en `CLIENT_SYSTEM_PROMPT` + stub `ADMIN_SYSTEM_PROMPT` (C2); `app/agent/admin_tools.py` con
> las 5 tools que envuelven `detect_all`/`sole_option_bottlenecks`/`solve+pareto`/`state` + perfil
> `ADMIN` (C3); `POST /admin/chat` bajo `require_admin` (C4, contrato en `docs/02` §Superficie 3.e);
> `tests/test_admin_chat.py` con 8 tests (C5). Ninguna admin tool contamina el `event_log`. Suite:
> **43 passed** (era 35). Solo queda **C6** (ML/DS: redactar `ADMIN_SYSTEM_PROMPT` real).

---

## B6 · Erradicar la carrera de sesión — *CONFIRMADO como bug real* · ✅ HECHO

**Diagnóstico verificado.** `app/agent/tools.py:42` guarda la sesión en un dict a nivel de
módulo:

```python
_current_session = {"id": "default"}
def set_session(session_id): _current_session["id"] = session_id
```

`run_agent` (`loop.py:89`) llama `set_session()` y luego hace **varias llamadas de red al LLM**
antes de que la tool lea el dict (`tools.py:138`, dentro de `event_log.record`). Dos `/chat`
concurrentes se pisan el dict global → los eventos quedan mal atribuidos. Esto envenena el
dashboard, que es tu evidencia de negocio.

**Fix (mínima cirugía): `contextvars.ContextVar`.** FastAPI corre cada request en su propia
tarea (anyio copia el contexto por tarea, también para endpoints `def` sincrónicos vía
threadpool), así que un `ContextVar` queda **aislado por request** sin pasar `session_id` a mano
por toda la cadena de tools.

```python
# tools.py
import contextvars
_current_session: contextvars.ContextVar[str] = contextvars.ContextVar(
    "session_id", default="default"
)
def set_session(session_id: str) -> None:
    _current_session.set(session_id)
# lectura:  session_id=_current_session.get()
```

Dos usos a cambiar: `tools.py:138` (`session_id=_current_session["id"]`) →
`_current_session.get()`.

> **Trade-off honesto:** el fix *estructuralmente correcto* es pasar `session_id` explícito hasta
> `event_log.record` y borrar el global. No se hace porque `registry.execute` invoca las tools de
> forma genérica (sin ese parámetro), y cambiar todas las firmas cuesta más de lo que aporta en un
> sprint. `ContextVar` es el punto correcto entre "arreglado" y "sobre-refactorizado". Deja un
> comentario diciendo justo esto, para que el juez de code quality no lo lea como pereza.

**Test (parte de B10):** lanzar 2 `/chat` con `session_id` distintos concurrentes y afirmar que
cada evento en `event_log` tiene el `session_id` correcto.

---

## B5 · Validación de arranque — *el backlog lo diagnosticó MAL* · ✅ HECHO

> **Aprovechar aquí (visible desde B8):** `main.py` usa `@app.on_event("startup")` (deprecado en
> FastAPI; sale como warning en los tests). B5 añadiría un tercer handler de arranque — mejor migrar
> los tres (`_load_history`, `_bootstrap_retrieval`, la validación nueva) a un único
> `@asynccontextmanager` en `lifespan=` de una vez, y así de paso se limpia la deuda.


**Corrección importante.** El backlog dice *"hoy cae a mock en silencio, viola la regla #3"*.
**Falso.** `gemini_provider.py:22-25` **revienta con `ValueError`** si la key está vacía. No hay
fallback silencioso. Verificado.

**El gap real es otro y es menor:** falla **perezosamente** — en el primer `/chat`, no al
arrancar — porque `factory.get_provider()` construye el provider bajo demanda. En una demo, "falla
en el primer mensaje delante del jurado" es casi tan malo como fallar en silencio.

**Propuesta (fail-fast en startup, ~10 min):** un hook de arranque que construya el provider una
vez y valide coherencia LLM ↔ retrieval. Si algo falta, el proceso no levanta.

```python
# main.py
@app.on_event("startup")
def _validate_providers() -> None:
    # Construye el provider ya: si falta la key de Gemini, revienta AQUÍ,
    # no en el primer /chat en medio de la demo.
    get_provider()
    # embedding_provider vacío hereda de llm_provider (config.py:17); si el
    # efectivo es gemini, exige la misma key.
    effective = (settings.embedding_provider or settings.llm_provider).lower()
    if effective == "gemini" and not settings.gemini_api_key:
        raise RuntimeError(
            "EMBEDDING/LLM en gemini sin GEMINI_API_KEY. Corrige .env o usa mock."
        )
```

> Nota: `_bootstrap_retrieval` (main.py:49) ya toca la capa de embeddings al arrancar, así que con
> Gemini probablemente ya fallaría temprano por ahí. Esta validación lo hace **explícito y con
> mensaje claro** en vez de dejar que reviente en las tripas del embedder.

---

## B3 · `POST /demo/reset` — *el backlog usó métodos que no existen con esa firma* · ✅ HECHO

**Corrección.** El backlog escribió `memory.reset(), tracer.clear()`. **No compila:** ambos son
**por-sesión**, no globales:

- `memory.py:54` → `reset(session_id)` · existe `all_ids()` (memory.py:57) para iterar.
- `tracing.py:37` → `clear(session_id)` · **no** hay limpieza global.
- `events.py:94` → `clear()` **sí** es global. ✅
- `state.py:36` → `reload_graph()` existe. ✅

**Ajuste para que sea posible — añadir dos métodos globales:**

```python
# memory.py (MemoryStore)
def reset_all(self) -> None:
    self._sessions.clear()

# tracing.py (Tracer)
def clear_all(self) -> None:
    self._traces.clear()
```

**Endpoint (protegido por B1):**

```python
class ResetRequest(BaseModel):
    keep_history: bool = True   # no borrar las 400 sesiones del dashboard por defecto

@app.post("/demo/reset", tags=["admin"])
def demo_reset(req: ResetRequest, _: None = Depends(require_admin)) -> dict:
    memory.reset_all()
    tracer.clear_all()
    state.reload_graph()
    state.set_objective("balanced")          # vuelve al estado inicial de la demo
    if not req.keep_history:
        event_log.clear()
    return {"status": "reset", "history_conservado": req.keep_history}
```

> Decisión de diseño: resetear también el objetivo activo a `balanced`. Sin esto, un reset a mitad
> de ensayo deja el objetivo en `maximize_margin` y el "antes/después" de la demo no arranca limpio.

---

## B2 · `POST /admin/frontier` — *NO necesitas al encargado de ML/DS* · ✅ HECHO

**Respuesta directa a tu pregunta:** esto es 100% tu terreno. `pareto.py` es solver simbólico, no
ML. Todas las piezas ya existen: `pareto_frontier`, `frontier_payload`, `select_on_frontier`,
`BUSINESS_OBJECTIVES`, `bounds_over`. No hay nada que preguntarle a él.

**Decisión de input — CONFIRMADA:** el endpoint recibe **los mismos requerimientos que `/solve`**
(`SolveRequest`). Una frontera de Pareto es la frontera *de una solución concreta*, así que
necesita requerimientos de entrada; el backlog original dio un contrato solo de salida y ese hueco
queda cerrado aquí. Así el dashboard pide "la frontera del escenario que estoy demostrando" y pinta
la elección de cada objetivo sobre los mismos ejes.

```python
@app.post("/admin/frontier", tags=["admin"])
def admin_frontier(req: SolveRequest, _: None = Depends(require_admin)) -> dict:
    requirements = _requirements_from(req)   # reusar el bloque de /solve
    result = solve(state.graph, requirements)
    if not result.satisfiable:
        return {"status": "SIN_SOLUCION",
                "nucleo_insatisfacible": [r.name for r in result.unsat_core]}

    frontier = pareto_frontier(result.solutions)
    frontier_ids = {tuple(c.ids) for c in frontier}
    dominadas = [c for c in result.solutions if tuple(c.ids) not in frontier_ids]

    elegida = {}
    for key, obj in BUSINESS_OBJECTIVES.items():
        chosen, _ranking = select_on_frontier(frontier, obj)
        elegida[key] = {"ids": list(chosen.ids), "precio_cop": chosen.total_price_cop}

    return {
        "status": "OK",
        "frontera": frontier_payload(frontier),
        "dominadas": frontier_payload(dominadas),   # el front las pinta en gris
        "elegida_por_objetivo": elegida,             # el punto que salta al cambiar objetivo
    }
```

> Refactor previo barato: extrae el bloque que arma `requirements` en `/solve` (main.py:113-123) a
> un helper `_requirements_from(req)` y reúsalo aquí. Evita que las dos rutas diverjan.
>
> **Escenario de demo fijo:** define en el front (o en un preset) un body de requerimientos estable
> —el mismo con el que ensayas el "$6.04M → $7.96M"— para que la frontera no cambie entre ensayos.

---

## B1 · Auth de admin + login — *confirmado: se hace* · ✅ HECHO

Decisión tomada: hay auth **y** pantalla de login (el equipo lo quiere y es barato). **Alcance
acotado — no escale a usuarios:** un solo token compartido cubre toda la narrativa cliente/admin.
Nada de JWT, OAuth, tabla de usuarios ni roles. "Login" aquí = una pantalla que pide el token y lo
guarda en el cliente.

```python
# config.py  → añadir
admin_token: str = ""

# main.py
from fastapi import Header, Depends

def require_admin(x_admin_token: str = Header(default="")) -> None:
    if not settings.admin_token:
        raise RuntimeError("ADMIN_TOKEN vacío: arranque abortado.")  # ver nota
    if x_admin_token != settings.admin_token:
        raise HTTPException(401, "Token de administrador inválido.")
```

Aplicar `Depends(require_admin)` a **todo** `/admin/*` y `/demo/*`. Dejar **abiertos** `/chat`,
`/solve`, `/retrieval/suggest`, `/trace/{id}` (superficie de cliente).

> **Regla dura:** si `ADMIN_TOKEN` está vacío, el arranque falla (mételo en el hook de B5). Un
> token vacío que deja pasar a todo el mundo es peor que no tener auth. El front lo maneja como en
> [02-frontend-guia.md](02-frontend-guia.md) §Auth.

---

## Resto del backlog (sin cambios de diagnóstico)

| # | Qué | Nota |
|---|---|---|
| ❌ **B4** | ~~`StaticFiles(directory="web", html=True)`~~ — **NO APLICA.** El front es Next.js (`frontend/`) con servidor propio + Vercel; se integra por HTTP + CORS, no como estático montado en FastAPI. | **Cerrado 2026-07-25.** Ver checklist arriba. |
| ✅ **B7** | Handlers para `Exception` (500 limpio, sin stacktrace), `HTTPException` y `RequestValidationError`, todos con envelope `{"error": {...}}`. | **HECHO** — `tests/test_error_handling.py`. |
| ✅ **B8** | `Field(gt=0)` en `SolveRequest` (`power_kw`, `budget_cop`, `voltage`). Verificado: antes aceptaba negativos. | **HECHO** — `tests/test_solve_validation.py`. |
| **B9** | Logging estructurado: request id, endpoint, latencia, tools llamadas en `/chat`. Hoy no hay ni una línea. | Sirve para depurar a las 11:00. |
| **B10** | Tests con `TestClient`: `/health`, `/solve` válido/ inválido, `/admin/*` sin token → 401, `/demo/reset`, y **la carrera de B6**. | — |
| ✅ **B11** | Test de arquitectura con `ast`: falla si `app/graph/` o `app/solver/` importan `app.llm`/`app.agent`/`app.retrieval`. **Prueba mecánica de que el LLM no decide.** Implementado como **allowlist** (más estricto): el núcleo solo puede importar `app.graph`/`app.solver`. | **HECHO** — `tests/test_architecture.py`. |
| ✅ **B13** | `.env.example` con todas las variables + `run.sh` (Linux/macOS) y `run.ps1` (Windows). | **HECHO 2026-07-25.** ⚠️ Verificar el retrieval con Gemini real roza la capa de embeddings — eso es del encargado de ML/DS. Tú solo cableas las variables. |

## Decisión declarada (no descuido)

`GET /trace/{session_id}` queda **sin auth a propósito**: es la evidencia de arquitectura que
abres en vivo ante el jurado. Respuesta preparada si preguntan: *"la traza es pública por diseño,
es el mecanismo de auditoría; lo sensible serían datos del cliente y no hay ninguno"*.
