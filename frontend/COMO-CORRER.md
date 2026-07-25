# Cómo correr el frontend

Requisito: **Node.js 18+** (ideal 20 o 22) y `npm`.

El browser llama **directo** a la API (`NEXT_PUBLIC_API_BASE_URL`). El backend
ya tiene CORS; en local debe permitir `http://localhost:3000`.

## Backend (FastAPI) — necesario si `USE_MOCKS = false`

Desde la raíz de **Veritas** (no desde `frontend/`):

```bash
# una sola vez
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edita .env: ADMIN_TOKEN=... (obligatorio) y, si hace falta:
# CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger: http://127.0.0.1:8000/docs

## Solo el front (sin backend)

En `config/mocks.ts` pon `USE_MOCKS = true`.

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Abrir: http://localhost:3000

## Front + API real (demo)

1. Backend arriba en `:8000` (pasos de arriba).
2. En `config/mocks.ts`:
   ```ts
   export const USE_MOCKS = false;
   ```
3. Front:

```bash
cd frontend
cp .env.example .env.local
# .env.local debe tener:
# NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm install
npm run dev
```

- Cliente: http://localhost:3000  
- Admin: http://localhost:3000/admin/login → pegar el `ADMIN_TOKEN` del `.env` del backend

## Variables útiles

| Qué | Dónde |
|---|---|
| URL de la API (front) | `frontend/.env.local` → `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` |
| Orígenes CORS (back) | `Veritas/.env` → `CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000` |
| Mock vs real | `frontend/config/mocks.ts` → `USE_MOCKS` |
| Token admin | `Veritas/.env` → `ADMIN_TOKEN` (se pega en el login; no va en el front) |

## Deploy en Vercel

1. Importar el repo **Veritas** en Vercel.
2. **Root Directory:** `frontend`.
3. Variables de entorno:

| Name | Value (ejemplo) |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `https://tu-backend.ejemplo.com` |
| `NEXT_PUBLIC_ADMIN_TOKEN_HINT` | _(opcional, vacío)_ |

4. En el backend, suma el origen de Vercel a `CORS_ORIGINS`, por ejemplo:
   `https://tu-app.vercel.app` (y el dominio custom si lo hay).
5. `USE_MOCKS = false` en el commit que deploys.
6. Deploy. Login admin con el `ADMIN_TOKEN` del backend.

```bash
cd frontend
npx vercel          # preview
npx vercel --prod   # producción
```

## Otros comandos

```bash
npm run build       # build de producción
npm run start       # servir el build en :3000
npm run typecheck   # chequear TypeScript
```
