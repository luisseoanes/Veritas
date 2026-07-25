const STORAGE_KEY = "veritas.session_id";

function randomId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  return `sess-${Math.random().toString(36).slice(2)}-${Date.now().toString(36)}`;
}

/**
 * `session_id` de la conversación. Vive en `sessionStorage` para que un refresh
 * no le borre la memoria al agente. Nunca se muestra en la UI.
 */
export function getSessionId(): string {
  if (typeof window === "undefined") return "default";
  const existing = window.sessionStorage.getItem(STORAGE_KEY);
  if (existing) return existing;
  const created = randomId();
  window.sessionStorage.setItem(STORAGE_KEY, created);
  return created;
}

export function newSessionId(): string {
  const created = randomId();
  if (typeof window !== "undefined") window.sessionStorage.setItem(STORAGE_KEY, created);
  return created;
}

const ADMIN_STORAGE_KEY = "veritas.admin_session_id";

/** Sesión separada para el copiloto de admin: no comparte memoria con el cliente. */
export function getAdminSessionId(): string {
  if (typeof window === "undefined") return "admin-default";
  const existing = window.sessionStorage.getItem(ADMIN_STORAGE_KEY);
  if (existing) return existing;
  const created = `admin-${randomId()}`;
  window.sessionStorage.setItem(ADMIN_STORAGE_KEY, created);
  return created;
}

export function newAdminSessionId(): string {
  const created = `admin-${randomId()}`;
  if (typeof window !== "undefined") window.sessionStorage.setItem(ADMIN_STORAGE_KEY, created);
  return created;
}
