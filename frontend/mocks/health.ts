import type { HealthResponse } from "@/lib/api/types";

export function mockHealth(objetivoActivo: string): HealthResponse {
  return {
    status: "ok",
    brand: "WEG",
    llm_provider: "mock",
    graph: { componentes: 28, aristas: 121, reglas: 4 },
    eventos_registrados: 402,
    objetivo_activo: objetivoActivo,
  };
}
