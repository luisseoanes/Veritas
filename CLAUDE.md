# Veritas — AgentSprint by ReshapeX, Medellín 2026

Contexto persistente del repositorio **del evento**. Léelo antes de tocar código.

## Qué es este repo y qué es el otro

| Repo | Rol | Estado |
|---|---|---|
| **Veritas** (este) | El repositorio que se entrega y se juzga. Aquí se construye el día del evento. | Vacío: solo CI de release y `docs/`. |
| **ReshapeX** (`../ReshapeX`, remoto `HackathonScaffold`) | **Scaffold**: motor completo ya construido, probado y defendible. Se porta desde aquí. | Funcionando y verificado (ver §Estado del scaffold). |

`../ReshapeX/CLAUDE.md` y `../ReshapeX/docs/` son la fuente extendida: contexto oficial del
evento, backlog de backend y contrato de frontend. **No los dupliques aquí — consúltalos.**

- Evento: 25 de julio de 2026, 8:00 AM – 12:00 PM, Universidad EAFIT. ~3.5 h de build.
- Marca elegida: **WEG** (accionamientos industriales: motores, variadores, protección, cableado).
- ⚠️ **El reto se revela el día del evento.** La marca se elige antes; la consigna no.
  El dominio está aislado en dos archivos para poder re-apuntar en minutos:
  `app/graph/rules.py` (reglas) y `app/data/catalog.py` (componentes). Todo lo demás
  —grafo, solver, MUS, Pareto, agente, detectores— es agnóstico al dominio.

## La idea

Grafo de conocimiento que modela el catálogo como una red de **restricciones técnicas**, no
como una lista de productos. El agente **no busca — resuelve**: traduce la necesidad del cliente
a un CSP y lo entrega a un solver simbólico. **El LLM nunca elige la configuración final**, así
que es imposible por construcción que recomiende algo técnicamente inválido.

Tres consecuencias, y las tres están en código:

1. **Con solución** → **frontera de Pareto** (costo ↔ margen ↔ disponibilidad ↔ eficiencia).
   Los objetivos de negocio eligen un punto *sobre* la frontera, nunca sacan al cliente de ella.
2. **Sin solución** → **núcleo mínimo insatisfacible (MUS)** por eliminación: qué restricciones
   hacen imposible el problema, más las relajaciones y el mínimo viable real.
3. **Agregado** → esos fracasos se vuelven inteligencia de negocio (*"16 clientes chocaron con la
   misma restricción — falta producto de 22 kW a 220 V"*).

## Los 5 componentes del checklist técnico (20% de la nota)

Los jueces verifican que **funcionen**, no que estén nombrados.

| # | Componente | Dónde (tras el port) |
|---|---|---|
| 1 | Knowledge tool / grounding | `app/graph/store.py` — aristas derivadas de reglas · RAG en `app/retrieval/` |
| 2 | Tool calling | `app/agent/registry.py` + `app/agent/tools.py` — 6 tools |
| 3 | Memory | `app/agent/memory.py` — hechos acumulados y descartes por sesión |
| 4 | Orquestación / planning | `app/agent/loop.py` — multi-paso con traza, tope `max_agent_steps` |
| 5 | Guardrails | `app/solver/engine.py` — **el solver es el guardrail** |

## Arquitectura a portar

```
app/
  graph/        Grafo de conocimiento
    schema.py     Component, Configuration, Kind, SOLUTION_SLOTS
    rules.py      Reglas de compatibilidad  <- CAMBIAR AQUÍ si cambia el dominio
    store.py      KnowledgeGraph (networkx); deriva TODAS las aristas de rules.py
    queries.py    Centralidad, cuellos de botella (sole_option), articulación
  solver/       Capa neuro-simbólica  (núcleo: no importa nada fuera de app.graph/app.solver)
    requirements.py  Restricciones nombradas y RETIRABLES (habilitan el MUS)
    engine.py        solve() + find_unsat_core() + explain()
    pareto.py        Frontera + objetivos de negocio (4 presets)
  agent/        Agente
    registry.py, tools.py, memory.py, tracing.py, loop.py
  retrieval/    Capa RAG — prepara y respalda, NUNCA decide
    embedder.py   Embeddings agnósticos (mock | gemini), dos umbrales por longitud de corpus
    chunks.py     Troceo citable de PDF; las tablas NO entran (viven en el grafo)
    profiles.py   Corpus curado a mano: aplicación del cliente -> restricciones candidatas
    index.py      Chroma persistente; Chroma nunca calcula embeddings
  intelligence/ Inteligencia de negocio
    events.py     Log estructurado (JSONL, en memoria + disco)
    detectors.py  3 detectores, todos con campo `formula` visible
  llm/          Capa agnóstica al proveedor (mock | gemini) — Protocol + factory
  data/catalog.py  Catálogo semilla WEG (28 componentes)
  state.py      Grafo + objetivo de negocio activo + retrieval perezoso
  main.py       FastAPI
scripts/
  smoke_test.py        Verificación de punta a punta, sin API key
  generate_history.py  Histórico sintético para los detectores
  index_datasheets.py  Indexa PDFs de WEG en el vector store (RAG)
  ingest_weg.py        Extrae las TABLAS de esos mismos PDFs -> catálogo/grafo
tests/                 7 archivos pytest + test de arquitectura ejecutable
web/                   Frontend (pendiente)
```

### Las 6 tools, y por qué el orden importa

| Grupo | Tools | Qué puede hacer |
|---|---|---|
| **DECIDE** | `solve_configuration` | La única que produce recomendaciones |
| **EXPLICA** | `explain_configuration`, `check_compatibility`, `search_catalog` | Lee el grafo |
| **PREPARA** | `suggest_requirements`, `cite_datasheet` | RAG: propone restricciones y cita documentos |

Las dos de RAG no pueden armar una configuración ni por accidente: `suggest_requirements`
devuelve *restricciones* que el cliente confirma y el solver valida; `cite_datasheet` devuelve
*texto con página*. El smoke test verifica que ningún ID de producto ni precio sale de ellas.
Sin respaldo devuelven `SIN_COINCIDENCIAS` / `SIN_RESPALDO` / `SIN_CORPUS` — el umbral está en
el código, no en el criterio del modelo.

## Reglas innegociables

1. **Los números los calcula el código; el LLM solo interpreta.** Nunca pedirle una cifra al
   modelo. Cada oportunidad en `detectors.py` viaja con su campo `formula`.
2. **El LLM nunca elige la configuración.** Solo traduce lenguaje natural a argumentos de tool.
   Si esta regla se rompe, se pierde la garantía entera del sistema. Está **probada
   mecánicamente** por `tests/test_architecture.py` (allowlist de imports sobre el AST, con
   violación plantada que demuestra que el guard muerde).
3. **Cero mock en el camino crítico.** Datos sembrados sí (y declarados); lógica falsa no.
   `LLM_PROVIDER=mock` es solo para desarrollo — **nunca** durante la demo.
4. **Declarar lo sintético antes de que lo pregunten.** Los perfiles de cliente del histórico son
   sintéticos; los eventos son salidas auténticas del solver. `app/retrieval/profiles.py` es
   corpus curado a mano, no sale de documentación de WEG. El catálogo semilla es representativo,
   no un volcado oficial. Decirlo suma, ocultarlo hunde.
5. **Secretos en `.env`** (nunca commitear), commits frecuentes con mensajes reales desde el
   minuto 1 — el jurado revisa el historial.
6. **El RAG prepara y respalda; nunca decide.** Precios, potencias y stock salen del grafo —
   jamás de un texto recuperado. Por eso las filas de tabla se excluyen del índice vectorial.
7. **Solo fuentes públicas** (T&C §5): datasheets publicados y sitio web. Nada confidencial de
   empleadores o clientes.

## Convención de commits — obligatoria en este repo

`.github/workflows/release.yml` corre **semantic-release en cada push a `main`**, con preset
`conventionalcommits`. Un mensaje que no siga la convención no rompe nada, pero no genera
release y ensucia las notas.

```
feat: …      minor      fix: / perf: / refactor: / docs: / chore: / style: / test: / build: / ci:   patch
BREAKING CHANGE: …  o  feat!: …      major
```

Historial actual: `2d141ec` → `ed7e1e3` (scaffolding de CI). El primer commit de código va encima.

## Estado del scaffold (verificado hoy, 2026-07-25)

**Funcionando:**
- Grafo: **28 componentes / 121 aristas derivadas** de 4 reglas (motor 9, drive 8, protección 6,
  cable 5). Ninguna arista escrita a mano.
- Solver + MUS (minimalidad verificada), Pareto + 4 objetivos de negocio, 3 detectores.
- Loop de agente con 6 tools, API FastAPI con auth de admin, manejo de errores unificado,
  `/demo/reset`, `/admin/frontier`.
- Histórico: **402 eventos** en `data/generated/events.jsonl`.
- RAG sobre Chroma: 10 perfiles de aplicación indexados; `cite_datasheet` verificado contra PDF
  real (recupera con documento y página, devuelve `SIN_RESPALDO` fuera de tema).
- `python -m scripts.smoke_test` → **todas las verificaciones pasan**.
- `python -m tests.test_architecture` → **verde, y atrapa la violación plantada**.

**Gaps reales, confirmados contra el código (no contra la doc):**
- ⚠️ **`pytest` no está instalado en `.venv`** — los 7 archivos de tests no corren. Está en
  `requirements.txt`; falta `pip install pytest`. Arreglarlo **antes** del evento.
- ⚠️ `scripts/ingest_weg.py` dice que `app/data/catalog.py` carga
  `data/generated/weg_catalog.json` si existe. **No lo hace**: `load_graph()` solo usa
  `ALL_COMPONENTS` en código. O se cablea la carga, o se corrige el docstring.
- Falta el **`LICENSE` permisivo** (MIT/Apache-2.0/BSD/ISC) — es **requisito de premio** (T&C §7).
- UI de cliente (chat) y dashboard de admin: `web/` está vacío. Contrato de datos completo en
  `../ReshapeX/docs/02-frontend-guia.md`. La guía oficial pide reservar los **últimos ~35 min**
  para la demo clickeable.
- Backlog de backend abierto: B9 (logging estructurado), B10 (tests de API con `TestClient`),
  B4 (servir estáticos), B13 (`.env.example` + `run.ps1`). Ver `../ReshapeX/docs/01-backend-backlog.md`.
- Gemini nunca se probó con API key real: el smoke test corre en modo `mock`.
- Índice de hojas de datos arranca **vacío** — el agente lo declara (`SIN_CORPUS`).

## Comandos

Desde la raíz del proyecto portado (en el scaffold el venv vive en `../ReshapeX/.venv`):

```powershell
.\.venv\Scripts\python.exe -m scripts.smoke_test              # verificar el motor + RAG
.\.venv\Scripts\python.exe -m tests.test_architecture         # demo de jurado autocontenida
.\.venv\Scripts\python.exe -m pytest -q                       # requiere: pip install pytest
.\.venv\Scripts\python.exe -m scripts.generate_history --sessions 400
.\.venv\Scripts\python.exe -m scripts.index_datasheets --stats          # estado del RAG
.\.venv\Scripts\python.exe -m scripts.index_datasheets --dir data/raw   # indexar PDFs
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload   # API en :8000/docs
```

El índice vive en `data/generated/chroma/` (ignorado por git) y se reconstruye solo si cambia
el corpus o el embedder. Cambiar `LLM_PROVIDER` de `mock` a `gemini` invalida el índice y lo
reconstruye: los vectores de un embedder no son comparables con los de otro.

## Configuración

`.env` (copiar de `.env.example`, nunca commitear):

```env
LLM_PROVIDER=mock          # mock | gemini — en la demo SIEMPRE gemini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
EMBEDDING_PROVIDER=        # vacío = sigue a LLM_PROVIDER
MAX_AGENT_STEPS=8
BRAND=WEG
ADMIN_TOKEN=               # vacío => el proceso NO levanta (fail-closed)
```

La app **falla al arrancar** (no en el primer `/chat`) si: `gemini` sin key, embeddings en
`gemini` sin key, o `ADMIN_TOKEN` vacío. Es deliberado: fallar en medio de la demo es peor.

## Endpoints

| Método | Ruta | Auth | Para qué |
|---|---|---|---|
| GET | `/health` | — | Marca, proveedor, stats del grafo, objetivo activo |
| POST | `/chat` | — | Conversación con el asesor comercial |
| POST | `/solve` | — | Solver directo, sin LLM — prueba que la lógica no depende del modelo |
| GET | `/trace/{session_id}` | — | Qué decidió el agente y por qué (**público a propósito**: es el mecanismo de auditoría) |
| POST | `/retrieval/suggest` | — | Aplicación → restricciones candidatas, sin LLM |
| GET | `/admin/verify` | token | Login del front |
| GET | `/admin/dashboard` | token | Inteligencia de negocio en tiempo real |
| GET/POST | `/admin/objectives` · `/admin/objective` | token | Objetivo comercial activo |
| POST | `/admin/frontier` | token | Frontera de Pareto del escenario + punto elegido por cada objetivo |
| POST | `/demo/reset` | token | Estado inicial entre ensayos |
| GET | `/admin/bottlenecks` · `/graph/evidence?a=&b=` | token | Analítica del grafo |

Admin va con header `X-Admin-Token` (comparado con `secrets.compare_digest`). Errores con
envelope uniforme: `{"error": {"status": …, "message": …, "detalles": […]}}`.

## El momento de la demo

```powershell
curl -X POST localhost:8000/admin/objective -H "X-Admin-Token: $T" -H "Content-Type: application/json" -d '{"key":"customer_value"}'
curl -X POST localhost:8000/chat -H "Content-Type: application/json" -d '{"message":"Motor de 5.5 kW a 220V con arranque suave, presupuesto 8 millones"}'
# -> $6.040.000

curl -X POST localhost:8000/admin/objective -H "X-Admin-Token: $T" -H "Content-Type: application/json" -d '{"key":"maximize_margin"}'
# misma pregunta -> $7.930.000 — distinta, igual de válida, y también en la frontera de Pareto
```

Guion completo, pitch de 20 s y respuestas preparadas para el jurado: `../ReshapeX/docs/00-contexto-hackathon.md` §7–8.

## Cómo se puntúa (para decidir en qué gastar minutos)

Progress 30% · Innovation 30% · Technical Checklist 20% · Presentation 10% · Code Quality 10%.
Progress se puntúa por el **hito más alto**: 1 setup → 2 algo funciona → 3 demo en vivo →
**4 toda respuesta fundamentada por knowledge tools** (que es exactamente nuestra tesis).
Code Quality pregunta una sola cosa: *"¿funciona o está mockeado?"* — el mock pesado limita el
puntaje sin importar el estilo.
