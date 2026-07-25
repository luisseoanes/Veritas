/** Base de la API FastAPI. Requiere CORS en el backend cuando el origen es distinto. */
export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");

/** Solo texto de ayuda en el placeholder del login. NUNCA el token real. */
export const ADMIN_TOKEN_HINT = process.env.NEXT_PUBLIC_ADMIN_TOKEN_HINT ?? "";

export function apiUrl(path: string): string {
  if (!path.startsWith("/")) path = `/${path}`;
  return `${API_BASE_URL}${path}`;
}
