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
 * Ya no queda ningún endpoint pendiente: `POST /admin/chat` existe en
 * `app/main.py` (protegido por `X-Admin-Token`) y se verificó en vivo —
 * responde 401 sin token y ejecuta las tools de análisis con él.
 *
 * Se deja la palanca porque el escenario que la motivó puede repetirse: si el
 * front vuelve a adelantarse a un endpoint, ponerla en `true` degrada esa
 * acción a un mock avisado en vez de romper la demo entera.
 *
 * En `false` NO queda nada simulado en el camino de demo.
 */
export const MOCK_PENDING_ENDPOINTS = false;
