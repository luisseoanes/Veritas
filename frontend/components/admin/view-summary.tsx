"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { Badge } from "@/components/ui/badge";
import type { DashboardResponse } from "@/lib/api/types";
import { objectiveLabel } from "@/lib/demo";
import { formatNumber, formatPercent } from "@/lib/format";

import { CHART } from "./chart-tokens";
import {
  DashCard,
  DashCardSkeleton,
  DashError,
  DashPanel,
  DashSection,
} from "./dash-ui";

interface ViewSummaryProps {
  data: DashboardResponse | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

export function ViewSummary({ data, loading, error, onRetry }: ViewSummaryProps) {
  if (!data && loading) {
    return (
      <DashSection title="Resumen" subtitle="Cargando…">
        <div className="grid gap-4 md:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <DashCardSkeleton key={index} lines={2} />
          ))}
        </div>
      </DashSection>
    );
  }

  if (!data) {
    return (
      <DashSection title="Resumen">
        <DashError message={error ?? "Sin datos del dashboard."} onRetry={onRetry} />
      </DashSection>
    );
  }

  const { resumen, supuestos, eventos_analizados } = data;
  const total = Math.max(resumen.conversaciones_totales, 1);
  const resolvedPct = resumen.resueltas / total;
  const unmetPct = resumen.sin_solucion / total;

  const pieData = [
    { name: "Resueltas", value: resumen.resueltas, color: CHART.ok },
    { name: "Sin solución", value: resumen.sin_solucion, color: CHART.danger },
  ].filter((slice) => slice.value > 0);

  return (
    <>
      {error ? (
        <div className="mb-6">
          <DashError message={`El último refresco falló: ${error}`} onRetry={onRetry} />
        </div>
      ) : null}

      <DashSection
        title="Resumen operativo"
        subtitle={`${formatNumber(eventos_analizados)} eventos analizados · recalculado en vivo.`}
        actions={<Badge tone="accent">{objectiveLabel(resumen.objetivo_activo)}</Badge>}
      >
        {/* Bento: hero metric + distribución + secundarias */}
        <div className="grid gap-4 lg:grid-cols-12">
          <DashPanel className="flex flex-col justify-between lg:col-span-5 lg:!p-7">
            <div>
              <p className="text-[12px] font-medium text-dash-text-muted">Conversaciones totales</p>
              <p className="tnum mt-3 text-[clamp(3rem,5vw,3.75rem)] font-semibold leading-none tracking-tight text-dash-text">
                {formatNumber(resumen.conversaciones_totales)}
              </p>
              <p className="mt-3 text-[13px] leading-relaxed text-dash-text-aux">
                Volumen acumulado sobre el histórico demo y sesiones en vivo.
              </p>
            </div>

            <div className="mt-8 grid grid-cols-2 gap-6 border-t border-dash-border pt-6">
              <div>
                <p className="text-[12px] font-medium text-dash-text-muted">Resueltas</p>
                <p className="tnum mt-1.5 text-[1.75rem] font-semibold leading-none text-dash-ok">
                  {formatNumber(resumen.resueltas)}
                </p>
                <p className="tnum mt-1 text-[12px] text-dash-text-aux">
                  {formatPercent(resolvedPct, 0)}
                </p>
              </div>
              <div>
                <p className="text-[12px] font-medium text-dash-text-muted">Sin solución</p>
                <p className="tnum mt-1.5 text-[1.75rem] font-semibold leading-none text-dash-danger">
                  {formatNumber(resumen.sin_solucion)}
                </p>
                <p className="tnum mt-1 text-[12px] text-dash-text-aux">
                  {formatPercent(unmetPct, 0)}
                </p>
              </div>
            </div>
          </DashPanel>

          <DashPanel className="lg:col-span-7 lg:!p-7">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-[12px] font-medium text-dash-text-muted">Distribución</p>
                <p className="mt-1 text-[13px] text-dash-text-aux">
                  Resultado del solver sobre conversaciones reales.
                </p>
              </div>
              <div className="flex flex-wrap gap-4">
                <LegendDot color={CHART.ok} label="Resueltas" />
                <LegendDot color={CHART.danger} label="Sin solución" />
              </div>
            </div>

            <div className="relative mx-auto mt-2 h-[240px] w-full max-w-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData.length ? pieData : [{ name: "Sin datos", value: 1, color: CHART.dominated }]}
                    dataKey="value"
                    nameKey="name"
                    innerRadius="68%"
                    outerRadius="90%"
                    paddingAngle={2}
                    stroke="none"
                  >
                    {(pieData.length ? pieData : [{ color: CHART.dominated }]).map((slice, index) => (
                      <Cell key={index} fill={slice.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<PieTooltip />} />
                </PieChart>
              </ResponsiveContainer>
              <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                <p className="text-[11px] font-medium text-dash-text-aux">Total</p>
                <p className="tnum mt-0.5 text-[1.75rem] font-semibold leading-none text-dash-text">
                  {formatNumber(resumen.conversaciones_totales)}
                </p>
              </div>
            </div>

            <div className="mt-2 space-y-3">
              <ActivityRow
                label="Resueltas"
                value={resolvedPct}
                color={CHART.ok}
              />
              <ActivityRow
                label="Sin solución"
                value={unmetPct}
                color={CHART.danger}
              />
              <ActivityRow
                label="Tasa de conversión asumida"
                value={supuestos.tasa_conversion_asumida}
                color={CHART.frontier}
              />
            </div>
          </DashPanel>
        </div>
      </DashSection>

      <DashSection
        title="Supuestos declarados"
        subtitle="Impactos económicos calculados por código. Ninguna cifra proviene del modelo de lenguaje."
      >
        <DashCard className="!p-0 overflow-hidden">
          <div className="grid divide-y divide-dash-border md:grid-cols-3 md:divide-x md:divide-y-0">
            <AssumptionCell
              label="Tasa de conversión"
              value={formatPercent(supuestos.tasa_conversion_asumida)}
              hint="Multiplica la demanda direccionable en los detectores."
            />
            <AssumptionCell
              label="Umbral de bundle"
              value={formatNumber(supuestos.umbral_co_ocurrencia_bundle)}
              hint="Co-ocurrencias mínimas para proponer un kit."
            />
            <AssumptionCell
              label="Eventos en vivo"
              value={formatNumber(eventos_analizados)}
              hint="Materia prima de los tres detectores de oportunidad."
            />
          </div>
          <div className="border-t border-dash-border bg-dash-surface-2 px-6 py-4">
            <p className="text-[12px] font-medium text-dash-text-muted">Nota del backend</p>
            <p className="mt-1 text-[13px] leading-relaxed text-dash-text-muted">{supuestos.nota}</p>
          </div>
        </DashCard>
      </DashSection>
    </>
  );
}

function AssumptionCell({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <div className="px-6 py-5">
      <p className="text-[12px] font-medium text-dash-text-muted">{label}</p>
      <p className="tnum mt-2 text-[1.75rem] font-semibold leading-none tracking-tight text-dash-text">
        {value}
      </p>
      <p className="mt-2 text-[12px] leading-relaxed text-dash-text-aux">{hint}</p>
    </div>
  );
}

function ActivityRow({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between gap-3">
        <span className="text-[12px] text-dash-text-muted">{label}</span>
        <span className="tnum text-[12px] font-medium text-dash-text">
          {formatPercent(value, 0)}
        </span>
      </div>
      <div className="dash-bar-track">
        <div
          className="h-full rounded-full transition-[width] duration-500"
          style={{
            width: `${Math.max(0, Math.min(1, value)) * 100}%`,
            backgroundColor: color,
          }}
        />
      </div>
    </div>
  );
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="size-2 rounded-full" style={{ backgroundColor: color }} />
      <span className="text-[12px] text-dash-text-muted">{label}</span>
    </div>
  );
}

function PieTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ name?: string; value?: number; payload?: { color?: string } }>;
}) {
  if (!active || !payload?.[0]) return null;
  const item = payload[0];
  return (
    <div
      className="rounded-[var(--radius-control)] border border-dash-border px-3 py-2 text-[12px] shadow-[var(--elev-2)]"
      style={{ background: CHART.tooltipBg, color: "#0f172a" }}
    >
      <span
        className="mr-2 inline-block size-2 rounded-full"
        style={{ backgroundColor: item.payload?.color }}
      />
      {item.name}: <span className="tnum font-semibold">{formatNumber(item.value ?? 0)}</span>
    </div>
  );
}
