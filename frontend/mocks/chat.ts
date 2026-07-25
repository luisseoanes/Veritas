import type { ChatResponse, TraceStep } from "@/lib/api/types";

const REPLIES: Record<string, string> = {
  balanced:
    "Con 5.5 kW a 220 V, arranque suave y un techo de $8.000.000 hay configuración viable. " +
    "Propongo el motor W22 IE3 de 5.5 kW / 220 V con el variador CFW300 (rampa de arranque suave), " +
    "guardamotor MPW y cableado 4 mm². Total $6.040.000, con eficiencia 90,2 % y stock disponible. " +
    "El solver validó las cuatro restricciones: potencia, tensión, característica y presupuesto.",
  customer_value:
    "Configuración de mejor valor para ti: motor W22 IE3 5.5 kW / 220 V, variador CFW300 con arranque suave, " +
    "guardamotor MPW y cableado 4 mm². Total $6.040.000. Es el punto de menor costo dentro de la frontera: " +
    "no existe otra combinación válida más barata que además cumpla el arranque suave.",
  maximize_margin:
    "Para tu requerimiento de 5.5 kW a 220 V con arranque suave recomiendo el motor W22 IE4 premium con " +
    "variador CFW500, guardamotor MPW y cableado 4 mm². Total $7.930.000, eficiencia 93,1 %. " +
    "Sigue dentro de tu presupuesto de $8.000.000 y aporta mayor eficiencia a lo largo de la vida útil.",
  clear_inventory:
    "Configuración viable priorizando disponibilidad inmediata: motor W22 IE3 5.5 kW / 220 V, variador CFW300, " +
    "guardamotor MPW y cableado 6 mm². Total $6.500.000, todas las referencias con stock alto, " +
    "por lo que el despacho no depende de reposición.",
};

export function mockChat(message: string, sessionId: string, objetivo: string): ChatResponse {
  const now = new Date();
  const at = (offsetMs: number) => new Date(now.getTime() + offsetMs).toISOString();

  const trace: TraceStep[] = [
    {
      step: 1,
      kind: "llm",
      detail: {
        provider: "mock",
        text: "El cliente declara potencia, tensión, característica y presupuesto. Traduzco a restricciones.",
        tool_calls: [{ name: "solve_configuration" }],
      },
      timestamp: at(0),
    },
    {
      step: 2,
      kind: "tool",
      detail: {
        name: "solve_configuration",
        arguments: {
          power_kw: 5.5,
          voltage: 220,
          budget_cop: 8000000,
          features: ["soft_start"],
          require_stock: true,
        },
        result:
          '{"status":"OK","objetivo":"' +
          objetivo +
          '","elegida":{"ids":["MOT-W22-055-220","CFW300-B","MPW25-3","CAB-4MM"],' +
          '"total_price_cop":6040000,"total_margin_cop":1200000,"min_stock":4,"efficiency":90.2},' +
          '"frontera":6,"dominadas":11}',
      },
      timestamp: at(1200),
    },
    {
      step: 3,
      kind: "tool",
      detail: {
        name: "explain_configuration",
        arguments: { ids: ["MOT-W22-055-220", "CFW300-B"] },
        result:
          '{"aristas":[{"a":"MOT-W22-055-220","b":"CFW300-B","regla":"drive_cubre_potencia_y_tension"}]}',
      },
      timestamp: at(1900),
    },
    {
      step: 4,
      kind: "llm",
      detail: {
        provider: "mock",
        text: "Redacto la recomendación con las cifras que devolvió el solver. No invento precios.",
      },
      timestamp: at(2400),
    },
  ];

  return {
    session_id: sessionId,
    reply: REPLIES[objetivo] ?? REPLIES.balanced,
    business_objective: objetivo,
    trace: message ? trace : [],
    known_requirements: {
      power_kw: 5.5,
      voltage: 220,
      budget_cop: 8000000,
      features: ["soft_start"],
    },
  };
}
