import type { FrontierPoint, FrontierResponse } from "@/lib/api/types";

function point(
  ids: string[],
  cost: number,
  margin: number,
  availability: number,
  efficiency: number,
): FrontierPoint {
  return {
    ids,
    objectives: { cost, margin, availability, efficiency },
    total_price_cop: cost,
    total_margin_cop: margin,
    min_stock: availability,
  };
}

const FRONTERA: FrontierPoint[] = [
  point(["MOT-W22-055-220", "CFW300-B", "MPW25-3", "CAB-4MM"], 6040000, 1200000, 4, 90.2),
  point(["MOT-W22-055-220", "CFW300-C", "MPW25-3", "CAB-6MM"], 6500000, 1310000, 7, 90.8),
  point(["MOT-W22-075-220", "CFW300-C", "MPW32-4", "CAB-6MM"], 7100000, 1520000, 5, 91.6),
  point(["MOT-W22-IE4-055", "CFW500-A", "MPW32-4", "CAB-4MM"], 7930000, 1980000, 3, 93.1),
];

const DOMINADAS: FrontierPoint[] = [
  point(["MOT-W21-055-220", "CFW300-B", "MPW25-3", "CAB-4MM"], 6320000, 1010000, 3, 88.4),
  point(["MOT-W21-055-220", "CFW300-C", "MPW25-3", "CAB-6MM"], 6740000, 1120000, 3, 88.9),
  point(["MOT-W22-055-220", "CFW500-A", "MPW25-3", "CAB-6MM"], 7420000, 1290000, 2, 90.4),
  point(["MOT-W21-075-220", "CFW300-C", "MPW32-4", "CAB-6MM"], 7580000, 1180000, 2, 89.1),
  point(["MOT-W22-075-220", "CFW500-A", "MPW32-4", "CAB-6MM"], 7860000, 1460000, 2, 91.9),
];

export function mockFrontier(): FrontierResponse {
  return {
    status: "OK",
    frontera: FRONTERA,
    dominadas: DOMINADAS,
    elegida_por_objetivo: {
      balanced: { ids: FRONTERA[0].ids, precio_cop: 6040000 },
      customer_value: { ids: FRONTERA[0].ids, precio_cop: 6040000 },
      maximize_margin: { ids: FRONTERA[3].ids, precio_cop: 7930000 },
      clear_inventory: { ids: FRONTERA[1].ids, precio_cop: 6500000 },
    },
  };
}
