/**
 * Fachada única de datos. Ningún componente hace `fetch` suelto (§1.2.1).
 * El cambio mock/real se decide aquí a partir de `config/mocks.ts`.
 */
import { MOCK_PENDING_ENDPOINTS, USE_MOCKS } from "@/config/mocks";
import { mockApi } from "@/mocks";

import { ADMIN_CHAT_PATH, ApiError, DEMO_RESET_PATH, request } from "./client";
import type {
  AdminChatResponse,
  ChatResponse,
  DashboardResponse,
  DemoResetResponse,
  FrontierResponse,
  HealthResponse,
  ObjectivesResponse,
  SetObjectiveResponse,
  SimulateRequest,
  SimulateResponse,
  SolveRequest,
  TraceResponse,
  VerifyResponse,
} from "./types";

/** Resultado de un endpoint que puede no existir todavía en el backend. */
export interface PendingEndpointResult<T> {
  data: T;
  /** `true` = la respuesta la fabricó el front porque el backend aún no publica la ruta. */
  simulado: boolean;
}

export const api = {
  health: (signal?: AbortSignal): Promise<HealthResponse> =>
    USE_MOCKS ? mockApi.health() : request<HealthResponse>("/health", { signal }),

  chat: ({ message, session_id }: { message: string; session_id: string }): Promise<ChatResponse> =>
    USE_MOCKS
      ? mockApi.chat(message, session_id)
      : request<ChatResponse>("/chat", { method: "POST", body: { message, session_id } }),

  trace: (sessionId: string): Promise<TraceResponse> =>
    USE_MOCKS ? mockApi.trace(sessionId) : request<TraceResponse>(`/trace/${sessionId}`),

  verifyAdmin: (): Promise<VerifyResponse> =>
    USE_MOCKS ? mockApi.verifyAdmin() : request<VerifyResponse>("/admin/verify", { admin: true }),

  dashboard: (signal?: AbortSignal): Promise<DashboardResponse> =>
    USE_MOCKS
      ? mockApi.dashboard()
      : request<DashboardResponse>("/admin/dashboard", { admin: true, signal }),

  objectives: (signal?: AbortSignal): Promise<ObjectivesResponse> =>
    USE_MOCKS
      ? mockApi.objectives()
      : request<ObjectivesResponse>("/admin/objectives", { admin: true, signal }),

  setObjective: (key: string): Promise<SetObjectiveResponse> =>
    USE_MOCKS
      ? mockApi.setObjective(key)
      : request<SetObjectiveResponse>("/admin/objective", {
          method: "POST",
          body: { key },
          admin: true,
        }),

  /** El objetivo activo NO va en este body: vive en el servidor. */
  frontier: (scenario: SolveRequest, signal?: AbortSignal): Promise<FrontierResponse> =>
    USE_MOCKS
      ? mockApi.frontier()
      : request<FrontierResponse>("/admin/frontier", {
          method: "POST",
          body: scenario,
          admin: true,
          signal,
        }),

  /** `POST /demo/reset` — existe en Veritas. `keep_history` siempre `true` por defecto. */
  demoReset: async ({ keep_history = true }: { keep_history?: boolean } = {}): Promise<
    PendingEndpointResult<DemoResetResponse>
  > => {
    if (USE_MOCKS) return { data: await mockApi.demoReset(keep_history), simulado: true };
    const data = await request<DemoResetResponse>(DEMO_RESET_PATH, {
      method: "POST",
      body: { keep_history },
      admin: true,
    });
    return { data, simulado: false };
  },

  /** `POST /admin/simulate` — contrafactual: re-resuelve las ventas perdidas
   *  con un producto hipotético en el catálogo. No modifica nada en el backend. */
  simulate: (payload: SimulateRequest, signal?: AbortSignal): Promise<SimulateResponse> =>
    request<SimulateResponse>("/admin/simulate", {
      method: "POST",
      body: payload,
      admin: true,
      signal,
    }),

  /** Copiloto de admin, ya publicado por el backend en `ADMIN_CHAT_PATH`. */
  adminChat: async ({
    message,
    session_id,
  }: {
    message: string;
    session_id: string;
  }): Promise<PendingEndpointResult<AdminChatResponse>> => {
    if (USE_MOCKS) return { data: await mockApi.adminChat(message, session_id), simulado: true };
    try {
      const data = await request<AdminChatResponse>(ADMIN_CHAT_PATH, {
        method: "POST",
        body: { message, session_id },
        admin: true,
      });
      return { data, simulado: false };
    } catch (error) {
      if (error instanceof ApiError && error.isMissingEndpoint && MOCK_PENDING_ENDPOINTS) {
        return { data: await mockApi.adminChat(message, session_id), simulado: true };
      }
      throw error;
    }
  },
};

export { ADMIN_CHAT_PATH, ApiError, DEMO_RESET_PATH };
export * from "./types";
