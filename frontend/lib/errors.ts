import { ApiError } from "@/lib/api/client";

/** Mensaje honesto para la UI: qué falló y, si se sabe, qué hacer. */
export function describeError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.isOffline) return error.message;
    if (error.isServerMisconfigured) {
      return `Backend mal configurado: ${error.message}`;
    }
    if (error.isMissingEndpoint) {
      return `El backend todavía no publica esta ruta (${error.status}).`;
    }
    return error.message;
  }
  if (error instanceof Error) return error.message;
  return "Ocurrió un error inesperado.";
}

export function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}
