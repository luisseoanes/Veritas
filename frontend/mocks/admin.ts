import type {
  AdminChatResponse,
  ObjectivesResponse,
  SetObjectiveResponse,
} from "@/lib/api/types";
import { formatCop } from "@/lib/format";

import { mockDashboard } from "./dashboard";

/** Objetivo activo simulado: permite ensayar el interruptor de la demo sin backend. */
let activeObjective = "balanced";

export function readMockObjective(): string {
  return activeObjective;
}

const OPTIONS: ObjectivesResponse["disponibles"] = [
  {
    clave: "balanced",
    etiqueta: "Equilibrado (por defecto)",
    pesos: { cost: 0.4, efficiency: 0.3, availability: 0.2, margin: 0.1 },
  },
  {
    clave: "customer_value",
    etiqueta: "Mejor valor para el cliente",
    pesos: { cost: 0.6, efficiency: 0.4 },
  },
  {
    clave: "maximize_margin",
    etiqueta: "Maximizar margen",
    pesos: { margin: 0.7, cost: 0.15, efficiency: 0.15 },
  },
  {
    clave: "clear_inventory",
    etiqueta: "Liberar inventario",
    pesos: { availability: 0.65, cost: 0.25, efficiency: 0.1 },
  },
];

export function mockObjectives(): ObjectivesResponse {
  return {
    activo: activeObjective,
    disponibles: OPTIONS,
    garantia:
      "Los objetivos solo eligen un punto DENTRO de la frontera de Pareto. Ninguna configuración " +
      "dominada es alcanzable, sea cual sea el objetivo.",
  };
}

export function mockSetObjective(key: string): SetObjectiveResponse {
  const option = OPTIONS.find((candidate) => candidate.clave === key) ?? OPTIONS[0];
  activeObjective = option.clave;
  return { activo: option.clave, etiqueta: option.etiqueta, pesos: option.pesos };
}

/**
 * Copiloto de admin simulado. Responde con cifras que salen del mismo mock del
 * dashboard, para no inventar números distintos de los que muestra la UI.
 */
export function mockAdminChat(
  message: string,
  sessionId: string,
  objetivo: string,
): AdminChatResponse {
  const report = mockDashboard(objetivo);
  const topDemand = report.demanda_no_satisfecha[0];
  const topRisk = report.riesgo_de_inventario[0];
  const normalized = message.toLowerCase();

  let reply: string;
  if (normalized.includes("inventario") || normalized.includes("stock") || normalized.includes("riesgo")) {
    reply =
      `El mayor riesgo de inventario es ${topRisk.nombre} (${topRisk.componente}): ${topRisk.stock} ` +
      `unidades en stock, única opción para ${topRisk.unica_opcion_para} configuraciones e índice ` +
      `${topRisk.indice_riesgo}. Exposición estimada ${formatCop(topRisk.exposicion_cop)}. ` +
      `Fórmula: ${topRisk.formula}`;
  } else if (normalized.includes("bundle") || normalized.includes("kit")) {
    const bundle = report.brechas_de_bundle[0];
    reply =
      `La brecha de bundle más rentable es "${bundle.nombres.join(" + ")}": ${bundle.co_ocurrencias} ` +
      `co-ocurrencias y un impacto estimado de ${formatCop(bundle.impacto_estimado_cop)}. ` +
      `Fórmula: ${bundle.formula}`;
  } else if (normalized.includes("objetivo")) {
    reply =
      `El objetivo activo es "${objetivo}". Cambiarlo mueve el punto elegido dentro de la frontera de ` +
      `Pareto, nunca fuera: ninguna configuración dominada es alcanzable con ningún objetivo.`;
  } else {
    reply =
      `Sobre ${report.eventos_analizados} conversaciones analizadas: ${report.resumen.resueltas} resueltas y ` +
      `${report.resumen.sin_solucion} sin solución. La oportunidad más grande es una ${topDemand.naturaleza} ` +
      `que afecta a ${topDemand.clientes_afectados} clientes, con demanda direccionable de ` +
      `${formatCop(topDemand.demanda_direccionable_cop)}. Fórmula: ${topDemand.formula}`;
  }

  return {
    session_id: sessionId,
    reply,
    business_objective: objetivo,
    trace: [
      {
        step: 1,
        kind: "tool",
        detail: {
          name: "read_dashboard",
          arguments: {},
          result: `{"eventos_analizados":${report.eventos_analizados},"detectores":3}`,
        },
        timestamp: new Date().toISOString(),
      },
    ],
  };
}
