import type { SolveRequest } from "@/lib/api/types";

/** Mensaje del guion. Existe como constante para ensayos y tests, no como botón en la UI. */
export const DEMO_MESSAGE = "Motor de 5.5 kW a 220V con arranque suave, presupuesto 8 millones";

/** Escenario técnico del guion: reusarlo mantiene la frontera estable entre ensayos. */
export const DEMO_FRONTIER_BODY: SolveRequest = {
  power_kw: 5.5,
  voltage: 220,
  budget_cop: 8_000_000,
  features: ["soft_start"],
  require_stock: true,
};

/** Assets de marca centralizados (§3.3). */
export const BRAND = {
  logoSrc: "/brand/logo.png",
  heroVideoUrl: "https://static.weg.net/medias/hc0/ha5/banner_video_WEGmotion_drives_1.mp4",
  heroImageUrl: "https://static.weg.net/medias/images/h56/hbf/See-_banner_site_1920x1080_5.webp",
} as const;

/** Etiquetas de objetivo para pintar el chip cuando solo tenemos la clave. */
export const OBJECTIVE_LABELS: Record<string, string> = {
  balanced: "Equilibrado",
  customer_value: "Mejor valor para el cliente",
  maximize_margin: "Maximizar margen",
  clear_inventory: "Liberar inventario",
};

export function objectiveLabel(key: string | undefined | null): string {
  if (!key) return "—";
  return OBJECTIVE_LABELS[key] ?? key;
}
