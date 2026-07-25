# Frontend — contrato funcional (para el desarrollador de front)

> **Esto NO dicta diseño.** Framework, scaffold, estética, tipografía y colores son 100% tu
> decisión. Este documento solo define **qué superficies se necesitan** y **cómo habla el backend**
> — el contrato de datos. Todo lo visual es tuyo.
>
> Para el hackathon el mínimo son **3 superficies: banner, chatbot y dashboard.**

## Contexto en una línea

Backend FastAPI ya funcionando. Dos audiencias sobre el mismo motor:
- **Cliente** (abierto): conversa con un asesor comercial → el agente resuelve una configuración.
- **Administrador** (con token): cambia el objetivo de negocio y ve inteligencia en vivo.

El **momento clave de la demo**: el admin cambia el objetivo → la misma pregunta del cliente
devuelve otra recomendación, y el punto se mueve **sobre la frontera de Pareto** (ambas válidas).

## Cómo se sirve el front

**Dos servidores, integración por HTTP + CORS.** El front es una app **Next.js** (`frontend/`) con
su propio servidor: en dev corre en `:3000` (`npm run dev`) y en prod se despliega en **Vercel**. El
navegador llama **directo** a la API vía `NEXT_PUBLIC_API_BASE_URL` (`http://localhost:8000` en
local). El backend **no** monta el front.

> ℹ️ **Cambio de arquitectura (2026-07-25):** la idea original de servir un build estático desde
> FastAPI (`/ui`, tarea B4) **quedó descartada** — este front no es un estático (`next.config.ts`
> sin `output: 'export'`). Se **cerró B4 como "no aplica"**; la integración es CORS (dev) + Vercel
> (prod). Detalles de arranque en `frontend/COMO-CORRER.md`.

> ✅ **CORS habilitado (2026-07-25):** el backend acepta peticiones desde **`http://localhost:3000`**
> (y `http://127.0.0.1:3000`), con `X-Admin-Token` entre los headers permitidos y `credentials`
> activado. Para otro puerto/origen (p.ej. el dominio de Vercel), añádelo a `CORS_ORIGINS` en el
> `.env` del backend (lista separada por comas).

Base de la API: **`http://localhost:8000`** · docs interactivas en **`/docs`** (Swagger, úsalas
para ver y probar cada payload real).

**Formato de error (uniforme).** Cualquier respuesta de error —400, 401, 422, 500— llega con la
misma forma, así que puedes manejarla en un solo sitio:
```jsonc
{ "error": { "status": 401, "message": "Token de administrador invalido o ausente.",
             "detalles": [ ... ] } }   // "detalles" solo en validaciones 422
```
Guíate por el **código de estado HTTP**; `message` es texto para mostrar. El 500 trae un mensaje
genérico a propósito (el detalle real queda en el log del servidor, no se expone).

> **`X-Request-ID` (debugging).** Toda respuesta del backend trae el header `X-Request-ID`. El
> servidor loguea cada petición con ese mismo id (endpoint, status, latencia y, en el chat, las
> tools llamadas). Si algo falla, inclúyelo en el reporte de bug: sirve para correlacionar la
> request con su log del lado servidor. No hace falta mostrarlo en la UI.

---

## Superficie 1 · Banner

Cabecera persistente. Contenido funcional mínimo:
- Identidad del producto + marca activa.
- Conmutador **Cliente ⇄ Administrador**.
- Indicador del **objetivo de negocio activo** (se lee de casi cualquier respuesta; ver abajo).

Datos disponibles: **`GET /health`** *(ya existe)*
```json
{ "status": "ok", "brand": "WEG", "llm_provider": "mock",
  "objetivo_activo": "balanced", "eventos_registrados": 400,
  "graph": { "...": "..." } }
```

---

## Superficie 2 · Chatbot (cliente — sin auth)

Chat de un turno por request. Tú mantienes el `session_id` (genera un UUID al abrir la sesión y
reúsalo en cada mensaje; así el agente recuerda el contexto).

**`POST /chat`** *(ya existe)*
```jsonc
// request
{ "message": "necesito mover una banda transportadora, 220V", "session_id": "abc-123" }

// response
{
  "session_id": "abc-123",
  "reply": "texto del asesor para pintar en la burbuja",
  "business_objective": "balanced",
  "trace": [ /* pasos: llm/tool, con qué se llamó y qué devolvió */ ],
  "known_requirements": { "voltage": 220 }   // lo que el agente ya sabe del cliente
}
```

**Panel de evidencia (diferenciador).** `reply` es la respuesta; `trace` es **cómo** el agente
llegó a ella (qué tool llamó, con qué argumentos, qué devolvió). Muéstralo colapsable ("ver
razonamiento") — es lo que prueba al jurado que no está mockeado. También en:

**`GET /trace/{session_id}`** *(ya existe)* — misma traza, por si la quieres refrescar aparte.

> El backend puede devolver `reply` con estados especiales dentro de las tools (p.ej.
> `SIN_SOLUCION` con núcleo insatisfacible, `SIN_RESPALDO`). No necesitas parsearlos: el `reply`
> ya viene redactado en lenguaje natural. La traza es opcional de renderizar en detalle.

---

## Superficie 3 · Dashboard (administrador — con token)

Todas las rutas `/admin/*` y `/demo/*` exigen el header **`X-Admin-Token`** (ver §Auth).

### a) Inteligencia en vivo — polling
**`GET /admin/dashboard`** *(ya existe)* — recalcula sobre los eventos acumulados en cada llamada.
Haz **polling cada ~2 s con `setInterval`** (nada de WebSockets). Trae los detectores de
oportunidad (cada uno con su `formula` visible) y un `resumen`:
```jsonc
{
  "resumen": { "conversaciones_totales": 412, "resueltas": 240,
               "sin_solucion": 172, "objetivo_activo": "balanced" },
  "...detectores...": []   // ver estructura real en /docs
}
```

### b) Cambiar el objetivo de negocio — el interruptor de la demo
**`GET /admin/objectives`** *(ya existe)* → lista `{clave, etiqueta, pesos}` + cuál está activo.
**`POST /admin/objective`** *(ya existe)*
```jsonc
{ "key": "maximize_margin" }   // balanced | customer_value | maximize_margin | clear_inventory
```
Tras esto, la siguiente llamada a `/chat` y a `/admin/frontier` reflejan el cambio.

### c) La frontera de Pareto — el gráfico estrella
**`POST /admin/frontier`** ✅ *(ya existe)*. Recibe los mismos
campos que `/solve` (los requerimientos del escenario que estás demostrando) y devuelve:
```jsonc
{
  "status": "OK",
  "frontera":  [ { "ids": [...], "objectives": { "cost": ..., "margin": ...,
                   "availability": ..., "efficiency": ... }, "total_price_cop": ... } ],
  "dominadas": [ /* misma forma — píntalas en gris, son inalcanzables */ ],
  "elegida_por_objetivo": {
    "balanced":        { "ids": [...], "precio_cop": 6040000 },
    "maximize_margin": { "ids": [...], "precio_cop": 7930000 }
  }
}
```
**Idea de visualización (tuya la ejecución):** un scatter 2D (ej. costo ↔ margen). Frontera
resaltada, dominadas en gris, y **el punto `elegida_por_objetivo` que salta** al cambiar el
objetivo en (b). Ese salto ES la demo.

> Input confirmado: recibe los mismos campos que `/solve`. La forma de la respuesta es estable;
> verifícala contra `/docs` cuando B2 esté implementado. Mientras tanto mockéala con lo de arriba
> para avanzar la UI.

### d) Reset de demo
**`POST /demo/reset`** ✅ *(ya existe)*
```jsonc
{ "keep_history": true }   // true = conserva las 400 sesiones del dashboard
```

### e) Chat del administrador — BI conversacional
**`POST /admin/chat`** ✅ *(ya existe — C4)* · exige `X-Admin-Token`.

Un segundo widget de chat, esta vez dentro del panel de admin. **Mismo formato de
request/response que `/chat`** (mismos campos: `message`, `session_id` → `reply`, `trace`,
`business_objective`, `known_requirements`), así que puedes **reutilizar el mismo componente de
chat** del cliente, cambiando solo la URL y añadiendo el header del token.

```jsonc
// request  (manda el header X-Admin-Token)
{ "message": "¿qué producto me falta y para cuántos clientes?", "session_id": "admin-abc-123" }

// response  (idéntico shape a /chat)
{ "session_id": "admin-abc-123", "reply": "...", "business_objective": "balanced",
  "trace": [ /* ... */ ], "known_requirements": {} }
```

Qué sabe hacer este chat (pregúntale en lenguaje natural): oportunidades/demanda insatisfecha,
cuellos de botella del catálogo, la frontera de Pareto de un escenario, el objetivo activo y
**cambiar el objetivo de negocio** (te pedirá confirmación antes de aplicarlo — es un cambio global
que afecta lo que el asesor del cliente recomienda).

> **Notas de integración:**
> - Usa un `session_id` **distinto** al del chat de cliente. El backend ya aísla las sesiones por
>   perfil (no se mezclan aunque coincida el id), pero mantenerlos separados en el front evita
>   confusión.
> - `GET /trace/{id}` es **solo para el chat de cliente**; no expone la traza del admin. La traza
>   del admin viene **inline** en el campo `trace` de la respuesta de `/admin/chat` — úsala de ahí.
> - Para el **momento clave del pitch**, cambiar el objetivo con el botón determinista
>   `POST /admin/objective` es más seguro que depender de que el modelo interprete la orden; usa el
>   chat-write como demo adicional, no como el mecanismo del que depende la demo.

### (opcional) Analítica del grafo
`GET /admin/bottlenecks`, `GET /graph/stats`, `GET /graph/evidence?a=&b=` — todas ya existen, por
si quieres enriquecer el dashboard.

---

## Auth (login de admin)

Modelo simple a propósito: **un solo token compartido**, no hay usuarios. *(backend: tarea B1.)*

1. Pantalla de login (solo para entrar a Administrador): pide el token, guárdalo en cliente
   (`localStorage`/estado). El diseño de esa pantalla es tuyo.
2. **Valida el token al enviarlo** con **`GET /admin/verify`** *(ya existe)*: manda el header y si
   responde `200 {"ok": true}` el token sirve; si `401`, muéstralo como error en el login. Así
   validas antes de entrar al panel, sin esperar a la primera llamada de datos.
3. En cada request a `/admin/*` y `/demo/*` manda el header `X-Admin-Token: <token>`.
4. Token inválido/ausente → **`401`**. Trátalo mostrando de nuevo el login.
4. La superficie de **Cliente no lleva token** — es pública.

---

## Estado de endpoints (para saber qué ya puedes integrar hoy)

| Superficie | Endpoint | Estado |
|---|---|---|
| Banner | `GET /health` | ✅ existe |
| Chatbot | `POST /chat`, `GET /trace/{id}` | ✅ existe |
| Dashboard | `GET /admin/dashboard`, `GET /admin/objectives`, `POST /admin/objective` | ✅ existe |
| Dashboard | `POST /admin/frontier` (gráfico Pareto) | ✅ existe (B2) |
| Dashboard | `POST /admin/chat` (chat BI del admin) | ✅ existe (C4) |
| Dashboard | `POST /demo/reset` | ✅ existe (B3) |
| Login | `GET /admin/verify` | ✅ existe |
| Todo admin | header `X-Admin-Token` + `401` | ✅ existe (B1) |

**Puedes arrancar hoy** con Banner + Chatbot + el objetivo del dashboard (todo ✅). El gráfico de
frontera y el reset se integran cuando backend cierre B2/B3 — mockéalos con los contratos de arriba
mientras tanto.

## Lo que es tuyo y no toco

Framework, bundler, estructura de `frontend/`, sistema de diseño, tipografía, **colores**, componentes,
estado, routing. Si quieres una referencia de marca del evento, el sitio oficial existe, pero
**no es una obligación** — decide tú. Este documento se queda en el *qué* y el *contrato de datos*.
