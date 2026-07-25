# AgentSprint (ReshapeX) 2026 — Contexto oficial del evento

> **Fuente:** sitio oficial <https://reshapeautomation.github.io/reshape_hackathon/>
> Documento reconstruido a partir de las **3 páginas** del sitio: la portada, la
> *Hackathon Guide* (embebida como `guide.html` en un iframe) y los *Términos y
> Condiciones* (`terminos-condiciones-hackathon.html`).
> **Capturado:** 2026-07-24. El sitio puede cambiar; verificar contra la fuente el día del evento.
>
> Todo lo de abajo es **texto oficial del organizador** salvo la sección final
> "Cómo nos posiciona", que es interpretación nuestra para este proyecto.

---

## 1. Datos duros del evento

| Campo | Valor |
|---|---|
| **Nombre** | AgentSprint by ReshapeX (*ReshapeX AgentSprint 2026*) |
| **Qué es** | El primer hackathon de agentes de IA en Medellín |
| **Fecha** | 25 de julio de 2026, 8:00 AM – 12:00 PM |
| **Lugar** | Universidad EAFIT, Medellín, Colombia |
| **Equipos** | 3–4 personas · entrada gratuita |
| **Duración del build** | ~3.5 horas (≈3:00–3:30 de build real) |
| **Organizador** | Reshape Automation Inc. (Delaware, EE. UU.) — <https://reshapeautomation.com> |
| **Tema** | Agentes de IA para **OEMs** (industria y más allá) |

### Premios (en efectivo, pagaderos el día del evento)

| Puesto | Premio (COP) |
|---|---|
| 🥇 1.º | $2.000.000 |
| 🥈 2.º | $1.000.000 |
| 🥉 3.º | $500.000 |

Personales, no transferibles, no canjeables. La entrega está **condicionada** a
cumplir los Términos, incluida la **publicación del código bajo licencia open-source
permisiva** (ver §5). Impuestos a cargo del ganador.

---

## 2. Cómo se puntúa — 5 dimensiones (texto oficial)

> "Los jueces puntúan a cada equipo en cinco dimensiones. Las cinco importan — un gran
> pitch sin sustancia técnica no gana, y tampoco un código fuerte que no se sabe explicar."

| Dimensión | Peso | Escala | Descripción oficial |
|---|---|---|---|
| **Progress** | **30%** | 1–4 pts · Objetivo | Se puntúa por el **hito más alto alcanzado**; cada nivel asume cumplidos los anteriores. |
| **Innovation** | **30%** | 1–10 · promedio 5 jueces | Qué tan **novedosa, creativa o inesperada** es la solución frente al enfoque obvio. Premia el caso de uso/flujo/experiencia que otros no habrían pensado. Originalidad tanto como ejecución. |
| **Technical Checklist** | **20%** | 0–5 pts · Revisión de arquitectura | Verifican si los **componentes clave de arquitectura de agente** están implementados y **funcionando** — no solo nombrados. Hasta 5 componentes; cada uno que demostrablemente hace su trabajo suma. *Nombrar un componente en un comentario no cuenta.* |
| **Presentation** | **10%** | 1–10 · promedio 5 jueces | No solo qué construiste, sino **qué tan claro lo explicas y qué tan bien vendes la idea**. Narrativa clara, entrega confiada, y respuestas que aguantan preguntas. |
| **Code Quality** | **10%** | 0–5 pts · Revisión de repo | Un juez técnico revisa el repositorio. Pregunta clave: **¿lo construido realmente funciona, o está mockeado?** Corrección, estructura limpia, manejo correcto de secretos, historial de commits trazable. **El mock pesado limita el puntaje** sin importar el estilo. |

### Los 4 hitos de "Progress" (texto oficial)

1. **Setup ready** — entorno listo.
2. **Something works** — algo funciona.
3. **Live demo** — demo en vivo.
4. **All answers grounded by knowledge tools** — toda respuesta fundamentada por herramientas de conocimiento.

> ⚠️ Ojo con el peso combinado: **Progress + Innovation = 60%**. Lo técnico verificable
> (Checklist + Code Quality) es 30%. Presentación 10%.

---

## 3. Marcas — "Pick your brand"

Cada equipo elige **una** marca. El organizador recomienda explorar productos, APIs y
documentación **antes** del evento: "cuanto más conozcas tu marca, más rápido construirás".

> ⚠️ **El reto específico se revela el día del evento** — la marca se elige antes, la consigna no.
> (Coincide con lo que ya sabíamos: nuestra marca es **WEG** — <https://www.weg.net>.)

Lista completa de marcas ofrecidas:

Sick · Banner · **WEG** · Teco · Pfannenberg · Pepperl+Fuchs · Lenze · LS Electric ·
Invertek · Balluff · LG · Decathlon · Logitech · Haceb · Bosch Tools · Corona ·
Michelin · Homecenter · Familia · Xiaomi · Éxito.

---

## 4. La *Hackathon Guide* oficial ("Building AI Agents")

> Guía de referencia del organizador. Tema: agentes de IA para OEMs. Formato ~3.5h.
> Revisada: julio 2026.

### La idea entera en tres frases (cita oficial)

> "Un agente de IA no es más que un modelo de lenguaje al que dejas **tomar acciones**, no
> solo chatear. Le das un objetivo y unas cuantas **herramientas** (cosas que puede hacer,
> como buscar en un catálogo de productos o llamar a la API de una empresa), y trabaja en
> un **bucle**: piensa, actúa, mira el resultado, repite, hasta que el trabajo está hecho."

Las tres piezas: **el modelo, las herramientas, y el bucle**.

### 01 · Conceptos definidos por el organizador

LLM · Prompt · Token · Ventana de contexto · API & API key · Agente · Tool/function
calling · **MCP** (Model Context Protocol, "USB-C para herramientas de IA") · **RAG**
(retrieval augmented generation) · Base de datos vectorial · **Guardrails** · Alucinación ·
Orquestación.

> Nota citable sobre alucinación (oficial): *"Es el principal riesgo en agentes de negocio,
> y la razón por la que fundamentarlo con RAG y herramientas importa tanto."*

### 02 · Cómo funciona un agente (el bucle)

1. Le das un **objetivo + herramientas**. Ej.: *"Encuentra el repuesto correcto para este
   modelo descontinuado"* + tool `search_catalog`.
2. El modelo **piensa**: "para emparejar el repuesto primero necesito las specs del viejo".
3. **Usa una tool**: llama `search_catalog("old part number")`; tu código la ejecuta y devuelve specs.
4. **Lee el resultado** y decide si necesita otra consulta o ya puede responder.
5. ↻ 2–4 se repiten hasta cumplir el objetivo.
6. ✓ **Responde**, fundamentado, no adivinado, con la fuente.

> Cita oficial que valida directamente nuestra tesis: *"Los agentes de este hackathon son
> herramientas de negocio para fabricantes y distribuidores, así que ser **correcto** importa
> mucho más que ser ingenioso. Un agente que inventa con confianza un número de parte es
> peor que inútil."*

### 03 · Qué necesitas de verdad

- Responder desde documentos (manuales, catálogos, políticas) → **modelo + RAG**. "La idea OEM clásica."
- Hacer algo en otro sistema (buscar orden, stock, abrir ticket) → **modelo + tools**.
- Razonar/redactar (resúmenes, correos, specs, traducciones) → **modelo + buen prompt**.
- Una mezcla → **modelo + tools + RAG**. Sigue siendo **un** agente.
- Trabajos separados que deben correr solos → múltiples agentes (rara vez vale la pena en ~3.5h).

> "El error más común es construir de más. Empieza con lo más pequeño que funcione."

### 04 · La caja de herramientas (picks por defecto)

| Rol en el bucle | Empieza aquí | Alternativas |
|---|---|---|
| **Modelo (cerebro)** | **Google Gemini** (gratis, sin tarjeta, texto+imagen) | Groq (gratis, rapidísimo, modelos abiertos tipo Llama) · Ollama (local, sin signup) · Claude/GPT (mejores, pero de pago) |
| **Construir el agente (loop)** | **Plain function calling** (tu propio loop con el SDK del modelo) | OpenAI Agents SDK / Claude Agent SDK · LangGraph (pesado, casi siempre overkill) |
| **Darle tools** | **Function calling** (integrado en todo modelo mayor) | MCP (reusar la tool entre apps) |
| **Darle conocimiento (RAG)** | **Chroma** (vectorial en pocas líneas) | Pinecone (managed) · LlamaIndex (carga PDFs y arma retrieval) |
| **Observabilidad** | **LangSmith** (ve cada paso y tool call; enciéndelo temprano) | — |
| **Demo** | **Streamlit / Gradio** (chat clickeable en pocas líneas de Python) | Next.js + Vercel AI SDK (más pulido, más trabajo) |

> Tips oficiales: elige un modelo y sigue (se cambia luego casi sin código) · un framework
> que tienes que aprender durante el hackathon suele costar más tiempo del que ahorra ·
> **salta RAG por completo si tu idea no depende de documentos** ("lo más fácil de sobre-construir") ·
> reserva los **últimos ~35 min para el demo** ("los jueces reaccionan a lo que pueden clickear, no a tu código").

### 05 · Cómo gastar tus ~3.5 horas (presupuesto oficial, equipo de 3–4)

| Bloque | Foco | Qué hacer |
|---|---|---|
| **Primeros 25 min** | Fijar la idea, juntos | Completar como grupo: *"Nuestro agente ayuda a ___ a hacer ___."* Luego dividir: uno cablea la llamada mínima al modelo mientras el resto reúne documentos/datos/APIs. |
| **~75 min** | Hacerlo útil, en paralelo | Uno cablea la tool/retrieval, otro limpia documentos/datos reales, un tercero arranca el shell del UI. Reagrupar a mitad para probar con preguntas reales. |
| **~50 min** | Hacerlo confiable, en paralelo | Uno agrega guardrails y maneja cómo se rompe, otro escribe preguntas trampa para romperlo, otro cablea citas de fuentes si usaron RAG. Merge y re-test juntos. |
| **Últimos ~35 min** | Hacerlo demoable, juntos | Uno termina el UI, el resto escribe y ensaya el show de 2 min. **Parar de construir features.** Todo el equipo debe saber el demo de memoria. |

> Dónde se van las mañanas (oficial): construir varios agentes cuando uno con buenas tools
> basta · todos amontonados en un laptop · una hora en hosting (un app local + un túnel tipo
> ngrok basta) · elegir un framework poco familiar porque "impresiona" · agregar RAG cuando la
> idea no necesita documentos · dejar el demo para los últimos 5 minutos.

### 06 · Antes del hackathon (checklist oficial)

- [ ] Instalar **Python 3.10+** (python.org).
- [ ] Obtener **API key gratis** en Google AI Studio (sin tarjeta). Guardarla en privado.
- [ ] Hacer una llamada "hello world" al modelo con esa key **antes** del día.
- [ ] Instalar herramienta de demo: `pip install streamlit` (o gradio) y abrir el ejemplo una vez.
- [ ] Opcional: instalar Ollama si quieres correr un modelo local.
- [ ] Tener listo tu **coding agent** (Claude Code, Cursor, Copilot…) instalado y con sesión iniciada **antes** de que arranque el reloj.
- [ ] Llegar con una idea aproximada y una frase de lo que hará tu agente.

> "Un mapa de inicio, no un reglamento. Las herramientas y los límites de free-tier cambian
> seguido; revisa cada sitio oficial antes de depender de él."

### Enlaces de la guía (recursos citados)

Gemini API · Google AI Studio · Groq · Ollama · Claude API / Agent SDK · OpenAI API /
Agents SDK · LangGraph · LangSmith · LlamaIndex · Chroma · Pinecone · MCP · Vercel AI SDK ·
Streamlit · Gradio · ngrok · python.org.

---

## 5. Términos y Condiciones — lo que impacta al proyecto

> Documento legal completo en `terminos-condiciones-hackathon.html`. Organizador:
> Reshape Automation Inc. (Delaware). Ley aplicable: **Colombia**, jueces de Medellín.
> Aquí solo las cláusulas que cambian decisiones técnicas o de conducta.

- **§5 Información de terceros (esencial):** prohibido usar, revelar, copiar o incorporar
  información confidencial, secretos, código, datos o IP de empleadores, clientes o
  instituciones. Igual la advertencia de la portada: *"No uses información confidencial de
  las empresas donde trabajas en tu agente o materiales de demo."*
  → Para nosotros: catálogo WEG **solo de fuentes públicas** (datasheets publicados, sitio web).
- **§6 Originalidad:** el proyecto debe ser original y respetar licencias de componentes de terceros.
- **§7 Propiedad intelectual:** el equipo **conserva** la titularidad del proyecto. **PERO**
  como condición para participar (y para cobrar premio) hay que **publicar el código fuente
  bajo licencia open-source permisiva** — MIT, BSD (2/3 cláusulas), Apache 2.0 o ISC.
  → **Acción pendiente:** añadir un `LICENSE` permisivo al repo antes del evento.
- **§8 Licencia al organizador:** licencia mundial, no exclusiva y gratuita para que ReshapeX
  reproduzca/exhiba/promocione el proyecto (no transfiere titularidad).
- **§9 Herramientas de terceros:** el participante es el único responsable de APIs, modelos,
  claves y **costos** que use. → Nuestras keys de Gemini y consumos corren por nuestra cuenta.
- **§10–11 Imagen y datos:** autorizas uso de imagen/voz y tratamiento de datos (Ley 1581/2012).
  Contacto de datos: legal@reshapex.com · política: <https://www.reshapex.com/en/dpa>.
- **§12 Premios:** los eligen miembros de ReshapeX según los criterios publicados; decisión
  **definitiva e inapelable**, sin obligación de justificarla.
- **§2 Elegibilidad:** mayores de 18 (o menor con autorización de representante legal).

---

## 6. Cómo nos posiciona *(interpretación nuestra — no es texto oficial)*

Cruce entre lo que pide el evento y lo que ya construimos (ver `CLAUDE.md`):

| Lo que premia el evento | Cómo lo cubre ReshapeX |
|---|---|
| **Progress nivel 4** — "toda respuesta fundamentada por knowledge tools" (30%) | Toda respuesta pasa por grafo de conocimiento + solver CSP. No hay respuesta sin fundamento estructural. |
| **Innovation** — "un caso/flujo que otros no habrían pensado" (30%) | Neuro-simbólico (CSP en vez de retrieval) + núcleo insatisfacible (MUS) + Pareto multi-stakeholder. El fracaso del agente como activo de negocio. |
| **Technical Checklist** — 5 componentes **funcionando**, no nombrados (20%) | 1 Knowledge/grounding · 2 Tool calling (6 tools) · 3 Memory · 4 Orquestación · 5 Guardrails (el solver **es** el guardrail). Cada uno en su módulo, verificado por el smoke test. |
| **Code Quality** — "¿funciona o está mockeado?" (10%) | Cero mock en el camino crítico; `LLM_PROVIDER=mock` solo en dev, nunca en demo. Secretos en `.env`. Commits frecuentes. `GET /trace/{session}` y `POST /solve` prueban que la lógica no depende del modelo. |
| **Presentation** (10%) | Demo del objetivo de negocio moviendo el punto sobre la frontera de Pareto ($6.04M → $7.96M, ambas válidas). |

**Alineaciones directas con la guía oficial:**
- Su ejemplo canónico del bucle es *"encuentra el repuesto correcto para este modelo
  descontinuado" → `search_catalog`* — exactamente nuestro dominio (accionamientos WEG).
- La guía insiste en que en B2B *"ser correcto importa más que ser ingenioso"* y que un agente
  que inventa un número de parte *"es peor que inútil"*. Nuestra tesis entera —**el LLM nunca
  elige la configuración, el solver la valida**— es la respuesta más fuerte posible a eso.
- Stack por defecto de la guía = nuestro stack: **Gemini + function calling + Chroma + demo**.
  Nuestra capa RAG (Chroma) es agnóstica (mock | gemini), igual que sugiere el organizador.

**Acciones pendientes que estos términos/guía hacen explícitas:**
- [ ] Añadir `LICENSE` permisivo (MIT/Apache-2.0) al repo — es **requisito de premio** (§7).
- [ ] Confirmar que todo el catálogo WEG sale de **fuentes públicas** (§5).
- [ ] Tener el demo (Streamlit/Gradio o el UI de cliente pendiente) clickeable — la guía y el
  peso de Presentation lo exigen; reservar los últimos ~35 min para ensayarlo.
- [ ] Probar Gemini con API key real antes del día (hoy el smoke test corre en modo mock).

---

## 7. Pitch y respuestas preparadas *(material de presentación)*

### Pitch (20 s)

> Las empresas pierden ventas y ni siquiera saben cuáles. Nuestro agente no busca productos:
> **resuelve** un problema de restricciones sobre un grafo de conocimiento, así que no puede
> alucinar una configuración inválida. Y cuando no existe solución, te dice **exactamente qué
> restricción** la hizo imposible. Esos fracasos, agregados, le dicen a la empresa qué producto
> le falta, a qué precio y para cuántos clientes.

### Preguntas del jurado — respuestas preparadas

**"¿No es manipular al cliente que el negocio dirija las recomendaciones?"**
No. El grafo es restricción dura y la frontera de Pareto es el conjunto elegible. Los objetivos
solo eligen un punto *dentro* de la frontera; una solución dominada es inalcanzable sea cual sea
el objetivo. Mostrar `select_on_frontier()` en `app/solver/pareto.py`.

**"¿Esto está mockeado?"**
`GET /trace/{session}` muestra qué tool se llamó y qué devolvió. `python -m scripts.smoke_test`
verifica el motor completo sin API key. `POST /solve` prueba que la lógica no depende del modelo.

**"¿Por qué grafo y no una base vectorial?"**
El detector de riesgo de inventario: cruza estructura del grafo (qué componente es única opción
compatible para otros) con demanda observada. Un embedding sabe que dos productos se parecen;
solo un grafo sabe que si un contactor se agota, N configuraciones dejan de existir.
Hay base vectorial (Chroma), pero **en otra capa**: entiende cómo habla el cliente y respalda
la prosa con documentación citable. La decisión no la toca.

**"¿Y el RAG no puede alucinar igual?"**
Puede recuperar el fragmento equivocado — eso sí. Lo que no puede es producir una configuración
inválida, porque no produce configuraciones: produce restricciones que el solver valida. Si el
embedding se equivoca de perfil, el cliente lo corrige al confirmarlo, o el solver lo declara
insatisfacible. Y si no hay respaldo documental, `cite_datasheet` devuelve `SIN_RESPALDO` en vez
del fragmento menos malo — el umbral está en el código, no en el criterio del modelo.

---

## 8. Demo (guion a ensayar)

1. Cliente pregunta → agente resuelve → mostrar el rastro de evidencia (`explain_configuration`).
2. Admin activa `maximize_margin` en `POST /admin/objective`.
3. Cliente pregunta lo mismo → **la recomendación cambia** ($6.04M → $7.96M), ambas válidas,
   ambas en la frontera.
4. `GET /admin/dashboard` se actualiza en vivo con la oportunidad nueva.

> La guía oficial pide reservar los **últimos ~35 min** para el demo y ensayarlo — "los jueces
> reaccionan a lo que pueden clickear, no a tu código" (ver §4).

---

## 9. Referencias de investigación *(citables en el pitch)*

- **ConstraintLLM: A Neuro-Symbolic Framework for Industrial-Level Constraint Programming** —
  <https://arxiv.org/html/2510.05774>
- **A Reality Check of Language Models as Formalizers on CSPs** — <https://arxiv.org/pdf/2505.13252>
- **A Pareto-Efficient Algorithm for Multiple Objective Optimization in E-Commerce
  Recommendation** (RecSys) — <https://dl.acm.org/doi/10.1145/3298689.3346998>
- **Multi-Objective Recommender Systems: Survey and Challenges** — <https://ceur-ws.org/Vol-3268/paper1.pdf>

> ⚠️ Las cifras tipo *"62% menos alucinaciones con GraphRAG"* vienen de blogs de vendors, no de
> papers revisados. Usarlas solo como contexto de mercado, nunca como dato duro.
