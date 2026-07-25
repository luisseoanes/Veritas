/**
 * Mocks de desarrollo. Implementan exactamente los tipos de `lib/api/types.ts`.
 *
 * Declarado sin ambigüedad: estos datos son fabricados para maquetar la UI sin
 * backend. En la demo `config/mocks.ts` va en `false` y todo sale del solver real.
 */
import type {
  AdminChatResponse,
  ChatResponse,
  DashboardResponse,
  DemoResetResponse,
  FrontierResponse,
  HealthResponse,
  ObjectivesResponse,
  SetObjectiveResponse,
  TraceResponse,
} from "@/lib/api/types";

import { mockChat } from "./chat";
import { mockDashboard } from "./dashboard";
import { mockFrontier } from "./frontier";
import { mockHealth } from "./health";
import { mockAdminChat, mockObjectives, mockSetObjective, readMockObjective } from "./admin";

const LATENCY_MS = 380;

function delay<T>(value: T, ms = LATENCY_MS): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

export const mockApi = {
  health: (): Promise<HealthResponse> => delay(mockHealth(readMockObjective())),
  chat: (message: string, sessionId: string): Promise<ChatResponse> =>
    delay(mockChat(message, sessionId, readMockObjective()), 900),
  trace: (sessionId: string): Promise<TraceResponse> =>
    delay({ session_id: sessionId, steps: mockChat("", sessionId, readMockObjective()).trace }),
  verifyAdmin: (): Promise<{ ok: boolean }> => delay({ ok: true }),
  dashboard: (): Promise<DashboardResponse> => delay(mockDashboard(readMockObjective()), 220),
  objectives: (): Promise<ObjectivesResponse> => delay(mockObjectives()),
  setObjective: (key: string): Promise<SetObjectiveResponse> => delay(mockSetObjective(key)),
  frontier: (): Promise<FrontierResponse> => delay(mockFrontier(), 620),
  demoReset: (keepHistory: boolean): Promise<DemoResetResponse> =>
    delay({ status: "reset", historico_conservado: keepHistory }),
  adminChat: (message: string, sessionId: string): Promise<AdminChatResponse> =>
    delay(mockAdminChat(message, sessionId, readMockObjective()), 800),
};

export { readMockObjective };
