const COP = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});

const DECIMAL = new Intl.NumberFormat("es-CO");

/** $6.040.000 — formato completo, para cifras que el jurado lee en detalle. */
export function formatCop(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return COP.format(value);
}

/** $6,04 M — formato compacto para ejes y labels grandes. */
export function formatCopCompact(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  if (Math.abs(value) >= 1_000_000_000) return `$${DECIMAL.format(round(value / 1_000_000_000, 2))} MM`;
  if (Math.abs(value) >= 1_000_000) return `$${DECIMAL.format(round(value / 1_000_000, 2))} M`;
  if (Math.abs(value) >= 1_000) return `$${DECIMAL.format(round(value / 1_000, 0))} k`;
  return COP.format(value);
}

export function formatNumber(value: number | null | undefined, maximumFractionDigits = 0): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("es-CO", { maximumFractionDigits }).format(value);
}

/** 0.15 → 15 % */
export function formatPercent(fraction: number | null | undefined, maximumFractionDigits = 0): string {
  if (fraction === null || fraction === undefined || Number.isNaN(fraction)) return "—";
  return new Intl.NumberFormat("es-CO", {
    style: "percent",
    maximumFractionDigits,
  }).format(fraction);
}

function round(value: number, decimals: number): number {
  const factor = 10 ** decimals;
  return Math.round(value * factor) / factor;
}

/** `budget_cop_8000000` → `budget cop 8000000`, para chips legibles del núcleo insatisfacible. */
export function humanizeConstraint(name: string): string {
  return name.replace(/_/g, " ");
}

export function formatTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleTimeString("es-CO", { hour12: false });
}
