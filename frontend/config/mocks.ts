/**
 * Palanca única mock/real. No hay toggle en la UI (§1.2.5).
 *
 *   false → todo sale del backend FastAPI real (valor de la demo).
 *   true  → todo sale de `mocks/*`, útil para maquetar sin backend arriba.
 *
 * Límite honesto: en Vercel este flag viaja en el bundle. Cambiarlo implica
 * redeploy; no existe "editar el archivo sin volver a desplegar".
 */
export const USE_MOCKS = false;

/**
 * Excepción declarada: `POST /admin/chat` aún no existe en `app/main.py`.
 * Con esto en `true`, esa acción cae a un mock local en vez de romper la demo;
 * la UI avisa que la respuesta es simulada. (`POST /demo/reset` ya existe.)
 */
export const MOCK_PENDING_ENDPOINTS = true;
