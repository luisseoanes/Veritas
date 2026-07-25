/**
 * Colores literales para Recharts (SVG no resuelve `var(--…)`).
 * Alineados al dashboard light: neutros + semántica escasa.
 */
export const CHART = {
  frontier: "#0064a6",
  frontierSoft: "#3d8fbf",
  dominated: "#94a3b8",
  chosen: "#0f172a",
  chosenFill: "#b45309",
  chosenHalo: "rgba(180, 83, 9, 0.18)",
  grid: "rgba(15, 23, 42, 0.06)",
  axis: "#94a3b8",
  surface: "#ffffff",
  surfaceSoft: "#f3f4f6",
  border: "rgba(15, 23, 42, 0.1)",
  tooltipBg: "#ffffff",
  ok: "#15803d",
  danger: "#b91c1c",
  accent2: "#475569",
  coral: "#b91c1c",
  pie: ["#0064a6", "#b91c1c", "#475569", "#b45309", "#15803d"],
} as const;
