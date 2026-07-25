/**
 * Recharts pinta atributos SVG y necesita valores concretos, no `var(--…)`.
 * Este archivo es el único lugar del front con colores literales y refleja
 * exactamente los tokens de `app/globals.css`. Si cambia allí, cambia aquí.
 */
export const CHART = {
  frontier: "#28b9da", // --dash-accent
  dominated: "#64748b", // --dash-dominated
  chosen: "#f1f1f8", // --dash-text (halo del punto elegido)
  chosenFill: "#28b9da", // --dash-accent
  grid: "rgba(241, 241, 248, 0.10)", // --dash-border
  axis: "#7d8ba3", // --dash-text-aux
  surface: "#0b1d3f", // --dash-surface
  border: "rgba(241, 241, 248, 0.20)", // --dash-border-strong
} as const;
