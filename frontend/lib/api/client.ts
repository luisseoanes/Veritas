import { forceReauth, getAdminToken } from "@/lib/admin-token";
import { API_BASE_URL } from "@/lib/env";

/**
 * Ruta del copiloto de administrador. Todavía no existe en `app/main.py`:
 * cuando el backend la publique con otro nombre, este es el único punto a cambiar.
 */
export const ADMIN_CHAT_PATH = "/admin/chat";

/** Ruta del reset de demo (tarea B3 del backlog de backend). */
export const DEMO_RESET_PATH = "/demo/reset";

export class ApiError extends Error {
  readonly status: number;
  readonly payload: unknown;

  constructor(status: number, message: string, payload?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }

  /** El backend no está arriba / no hay red. */
  get isOffline(): boolean {
    return this.status === 0;
  }

  /** El endpoint aún no existe en esta versión del backend. */
  get isMissingEndpoint(): boolean {
    return this.status === 404 || this.status === 405 || this.status === 501;
  }

  /** `require_admin` devuelve 500 cuando el servidor no tiene ADMIN_TOKEN configurado. */
  get isServerMisconfigured(): boolean {
    return this.status === 500;
  }
}

interface RequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
  /** Manda el header `X-Admin-Token`. El cliente nunca lleva token. */
  admin?: boolean;
  signal?: AbortSignal;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, admin = false, signal } = options;

  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";

  if (admin) {
    const token = getAdminToken();
    if (!token) {
      forceReauth();
      throw new ApiError(401, "Sesión de administrador no iniciada.");
    }
    headers["X-Admin-Token"] = token;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
      cache: "no-store",
    });
  } catch (cause) {
    if (cause instanceof DOMException && cause.name === "AbortError") throw cause;
    throw new ApiError(
      0,
      `No se pudo contactar la API en ${API_BASE_URL}. Verifica que el backend esté corriendo.`,
      cause,
    );
  }

  if (!response.ok) {
    const payload = await safeJson(response);
    if (response.status === 401 && admin) forceReauth();
    throw new ApiError(response.status, messageFrom(payload, response), payload);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

async function safeJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

/**
 * Normaliza los tres formatos de error que puede devolver el backend:
 * envelope propio `{error:{...}}`, `detail` de FastAPI (string) y `detail`
 * de validación de Pydantic (lista de `{msg}`).
 */
function messageFrom(payload: unknown, response: Response): string {
  if (payload && typeof payload === "object") {
    const record = payload as Record<string, unknown>;

    const envelope = record.error;
    if (envelope && typeof envelope === "object") {
      const message = (envelope as Record<string, unknown>).message;
      if (typeof message === "string") return message;
    }

    const detail = record.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) =>
          item && typeof item === "object" ? String((item as Record<string, unknown>).msg ?? "") : "",
        )
        .filter(Boolean);
      if (messages.length) return messages.join(" · ");
    }
  }

  if (response.status === 401) return "Token de administrador inválido o ausente.";
  if (response.status === 500) return "El servidor respondió con un error.";
  return response.statusText || `Error ${response.status}`;
}
