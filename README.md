# Veritas — Plataforma de Inteligencia Comercial Neuro-Simbólica

Agente comercial sobre un **grafo de conocimiento** + un **solver de restricciones**.
No busca productos: **resuelve** un problema de configuración.

> **AgentSprint by ReshapeX** · Universidad EAFIT, Medellín · 25 de julio de 2026
> Marca: **WEG** (accionamientos industriales) · Equipo **Capa 8**

## Pruébalo ahora

| | URL |
|---|---|
| **Aplicación (cliente + admin)** | https://veritas-frontend-production.up.railway.app |
| **API** | https://veritas-production-7952.up.railway.app |
| **Swagger** | https://veritas-production-7952.up.railway.app/docs |
| **Salud del sistema** | https://veritas-production-7952.up.railway.app/health |

El panel de administrador pide un token (`X-Admin-Token`). La superficie de cliente
es pública y no lo necesita.

## Qué hace distinto

| Enfoque habitual | Este sistema |
|---|---|
| RAG vectorial: recupera texto parecido | Grafo: recorre restricciones técnicas derivadas de reglas |
| El LLM elige el producto | **El solver elige**; el LLM solo traduce y explica |
| "No encontré nada" | **Núcleo mínimo insatisfacible**: qué restricción lo hizo imposible |
| Una recomendación | **Frontera de Pareto** con trade-offs explícitos |
| El agente responde texto | **Emite una cotización** con consecutivo y validez |
| Dashboard de métricas | Las ventas perdidas se vuelven **inteligencia de producto** |

**La garantía:** el LLM traduce lenguaje natural a *argumentos de una función*, nada
más. La configuración la decide el solver, los números los calcula el código y la
evidencia sale del grafo. Si el modelo alucina, alucina argumentos — y el solver los
rechaza. Por construcción no puede recomendar algo técnicamente inválido.

Y no es una promesa: [`tests/test_architecture.py`](tests/test_architecture.py) analiza
el AST y **falla** si `app/graph/` o `app/solver/` importan el LLM, el agente o el RAG.

## Los 6 pasos de una consulta

```
CONSULTA DEL CLIENTE
  1 ESCUCHA    RAG traduce "una banda en zona de lavado"
               → restricciones CANDIDATAS         (nunca productos)
  2 CONFIRMA   el cliente valida                  (nada se asume)
  3 TRADUCE    el LLM → argumentos de tool        ← aquí termina su poder
  ──────────────────────────────────────────────────────────────────
  4 RESUELVE   solver CSP sobre el grafo          ← aquí empieza la garantía
  5 DECIDE     Pareto → el negocio elige un punto DENTRO de la frontera
               o núcleo mínimo insatisfacible + alternativas con precio
  6 ACTÚA      cotización real · y el fracaso queda registrado
```

## Verificar que funciona (sin API key)

Tres comandos. Con la configuración por defecto de `.env.example`
(`LLM_PROVIDER=mock`), ninguno necesita clave de Gemini ni conexión a internet:
el solver, el grafo y los detectores **no dependen del modelo**. Eso mismo es la
prueba de que la lógica de negocio no vive en el prompt.

```bash
python -m tests.test_architecture   # el LLM no puede colarse en la decisión
python -m scripts.smoke_test        # motor + RAG de punta a punta
python -m pytest -q                 # 48 tests
```

**`test_architecture`** es una demo autocontenida: comprueba que el núcleo está
aislado **y** que el guard detecta una violación plantada a propósito. Un test que
solo sabe estar en verde podría estar roto y nadie lo notaría.

**`smoke_test`** verifica las seis cosas que hay que poder defender: que las aristas
se derivan de reglas, que el solver justifica sus soluciones, que la frontera de
Pareto no contiene dominadas, que los objetivos no salen de la frontera, que el
núcleo insatisfacible es **minimal**, y que del RAG no sale ningún ID de producto
ni ningún precio.

## Correr en local

```bash
./run.sh          # Linux / macOS
.\run.ps1         # Windows
```

Idempotente: crea el venv, instala dependencias, copia `.env` desde el ejemplo y
levanta la API en http://localhost:8000 (Swagger en `/docs`).

Frontend (Next.js 15, en otra terminal):

```bash
cd frontend && npm install && npm run dev     # http://localhost:3000
```

### Configuración

Copia `.env.example` a `.env`. Lo mínimo:

```env
LLM_PROVIDER=gemini            # 'mock' corre TODO el sistema sin API key
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.6-flash  # gemini-2.5-flash da 404 en cuentas nuevas
ADMIN_TOKEN=...                # vacío ⇒ el proceso NO levanta (fail-closed)
```

El proceso **falla al arrancar** —no en la primera consulta— si falta la key o el
token. Fallar en medio de una demo es peor que no arrancar.

## Estado verificado

| | |
|---|---|
| Grafo | **230 componentes · 2.277 aristas**, todas derivadas de 4 reglas |
| Catálogo | 171 productos **reales de WEG** + 59 de semilla |
| Documentación | **778 fragmentos** de 2 catálogos oficiales, citables con página |
| Histórico | 400 conversaciones (271 resueltas / 129 sin solución) |
| Tools | 15 registradas: 9 del asesor, 6 del analista |
| Tests | **48 pasando** |

## Arquitectura

La dependencia va en **una sola dirección**. El núcleo no conoce al LLM.

```
app/
  graph/          Grafo de conocimiento
    rules.py        Reglas de compatibilidad   ← CAMBIAR AQUÍ si cambia el dominio
    store.py        Deriva TODAS las aristas de rules.py; ninguna a mano
    queries.py      Cuellos de botella, articulación, centralidad
  solver/         Núcleo simbólico (no importa nada fuera de app.graph/app.solver)
    requirements.py Restricciones nombradas y RETIRABLES (habilitan el MUS)
    engine.py       solve() + find_unsat_core() + explain()
    pareto.py       Frontera + 4 objetivos de negocio
  agent/          Loop propio con traza (no el del SDK)
    tools.py        9 tools de cliente · quotes.py emite las cotizaciones
    admin_tools.py  6 tools de analista de negocio
    memory.py       Hechos acumulados y configuraciones descartadas
  retrieval/      RAG — prepara y respalda, NUNCA decide
  intelligence/   Detectores de oportunidad + simulador contrafáctico
  data/catalog.py Semilla WEG + carga del catálogo real extraído de los PDF
  main.py         FastAPI
frontend/         Next.js 15: chat de cliente (/) + dashboard admin (/admin)
```

### Las tools, y por qué el orden importa

| Grupo | Qué puede hacer |
|---|---|
| **DECIDE** | `solve_configuration` — la única que produce recomendaciones |
| **ACTÚA** | `generate_quote` — la única que cambia algo fuera del proceso |
| **EXPLICA** | `explain_configuration`, `check_compatibility`, `search_catalog`, `compare_products` |
| **RECUERDA** | `discard_configuration` — lo rechazado deja de ofrecerse |
| **PREPARA** | `suggest_requirements`, `cite_datasheet` — RAG |

Las dos de RAG no pueden armar una configuración ni por accidente: una devuelve
*restricciones* que el cliente confirma, la otra *texto con página*. Sin respaldo
devuelven `SIN_RESPALDO` / `SIN_CORPUS` en vez del fragmento menos malo — el umbral
está en el código, no en el criterio del modelo.

`generate_quote` lleva guardrail: **se niega a cotizar** una configuración que el
grafo no aprueba.

## El momento de la demo

```bash
# 1. Un problema imposible a propósito
POST /chat  "Motor de 22 kW a 440V con IP66 para zona de lavado, 30 millones"
# → SIN_SOLUCION + núcleo mínimo + BRECHA DE CATÁLOGO + 2 alternativas con precio

# 2. El cliente acepta una
POST /chat  "Acepto la opción sin IP66, emite la cotización"
# → COT-202607-XXXX

# 3. El administrador pregunta qué le falta al catálogo
POST /admin/chat  "¿Y si incorporo un motor de 22 kW a 220V a 8.5 millones?"
# → 0 recuperados: el variador que le sirve pide 130 A y tu protección
#   más grande llega a 125 A. La brecha no era un producto, eran dos.
```

Y el interruptor de política: `POST /admin/objective` cambia el objetivo comercial y
la misma pregunta devuelve **$6.040.000 → $7.960.000**. Distinta, igual de válida, y
ambas **en la frontera de Pareto**: el negocio elige el punto, la frontera elige el
conjunto, y el cliente nunca sale de ella.

## Honestidad sobre los datos

Se declara antes de que lo pregunten:

- **Reales de WEG:** número de parte, potencia, corriente, rango de voltaje y precio
  de lista USD de 171 variadores, extraídos de catálogos oficiales publicados en
  `static.weg.net`. Cada fila conserva la **página** de la que salió.
- **Supuesto nuestro:** la conversión USD→COP (la tasa viaja declarada en el JSON).
- **Representativo:** motores, protección y cables de la semilla, construidos sobre
  rangos públicos de las líneas WEG. Marcado como tal en `app/data/catalog.py`.
- **Simulado:** el stock. WEG no publica inventario.
- **Sintético:** los *perfiles* de cliente del histórico. Cada uno se resolvió con el
  solver de verdad sobre el grafo de verdad; los eventos —incluidos los núcleos
  insatisfacibles— son salidas auténticas del motor.
- **Curado a mano:** los 10 perfiles de aplicación de `app/retrieval/profiles.py`.
  Por eso su salida son *sugerencias que el cliente confirma*, nunca decisiones.

**La lógica nunca es representativa.** Reglas, solver, núcleo insatisfacible y Pareto
operan sobre estos datos exactamente igual que sobre los reales.

## Cambiar de dominio

Si el reto pide otra marca, solo se tocan dos archivos:

- [`app/graph/rules.py`](app/graph/rules.py) — las reglas de compatibilidad
- [`app/data/catalog.py`](app/data/catalog.py) — los componentes

Grafo, solver, MUS, frontera de Pareto, agente, RAG y detectores son agnósticos al
dominio.

## Despliegue

Dos servicios en Railway, mismo proyecto y entorno.

- **Backend:** conectado a GitHub, se redespliega solo en cada push a `main`.
- **Frontend:** `railway up frontend --path-as-root --service veritas-frontend`
  (un `git push` **no** lo actualiza).

El índice vectorial y el histórico se **versionan con el repo** (excepciones
declaradas en `.gitignore`): el contenedor arranca desde el repo y su disco es
efímero, así que sin eso cada despliegue tendría el dashboard vacío y
`cite_datasheet` en `SIN_CORPUS`. Las versiones de `requirements.txt` están fijadas
porque un `chromadb` distinto no podría leer ese índice.

## Documentación

- [`CLAUDE.md`](CLAUDE.md) — cómo trabajar en el código y las reglas innegociables
- [`docs/00-contexto-hackathon.md`](docs/00-contexto-hackathon.md) — contexto del evento, scoring, pitch
- [`docs/01-backend-backlog.md`](docs/01-backend-backlog.md) — backlog con diagnósticos verificados
- [`docs/02-frontend-guia.md`](docs/02-frontend-guia.md) — contrato de datos del frontend
- [`docs/03-chatbot-dual.md`](docs/03-chatbot-dual.md) — los dos perfiles de agente

## Licencia

[MIT](LICENSE).
