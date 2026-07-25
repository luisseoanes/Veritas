"use client";

import { Boxes, CircleCheck, CircleSlash, MessagesSquare, Percent } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { DashboardResponse } from "@/lib/api/types";
import { objectiveLabel } from "@/lib/demo";
import { formatNumber, formatPercent } from "@/lib/format";

import {
  DashCard,
  DashCardSkeleton,
  DashError,
  DashMetricBlock,
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
      <DashSection title="Resumen" subtitle="Cargando inteligencia en vivo…">
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <DashCardSkeleton key={index} lines={1} />
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

  return (
    <>
      {error ? (
        <div className="mb-6">
          <DashError message={`El último refresco falló: ${error}`} onRetry={onRetry} />
        </div>
      ) : null}

      <DashSection
        title="Resumen"
        subtitle={`${formatNumber(eventos_analizados)} eventos analizados · se recalcula en cada consulta sobre los eventos acumulados.`}
        actions={
          <Badge tone="accent" size="lg">
            {objectiveLabel(resumen.objetivo_activo)}
          </Badge>
        }
      >
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
          <DashMetricBlock
            className="xl:col-span-2"
            label="Conversaciones totales"
            value={formatNumber(resumen.conversaciones_totales)}
            icon={MessagesSquare}
            tone="accent"
            size="hero"
            hint="Cada conversación deja un evento estructurado: es la materia prima de los detectores."
          />
          <DashMetricBlock
            label="Resueltas"
            value={formatNumber(resumen.resueltas)}
            icon={CircleCheck}
            tone="ok"
            hint="El solver encontró al menos una configuración válida."
          />
          <DashMetricBlock
            label="Sin solución"
            value={formatNumber(resumen.sin_solucion)}
            icon={CircleSlash}
            tone="danger"
            hint="Restricciones incompatibles: cada caso viaja con su núcleo mínimo insatisfacible."
          />
        </div>
      </DashSection>

      <DashSection
        title="Supuestos declarados"
        subtitle="Los impactos económicos se calculan por código bajo estos supuestos. Ninguna cifra proviene del modelo de lenguaje."
      >
        <div className="grid gap-6 lg:grid-cols-2">
          <DashMetricBlock
            label="Tasa de conversión asumida"
            value={formatPercent(supuestos.tasa_conversion_asumida)}
            icon={Percent}
            tone="accent"
            hint="Multiplica la demanda direccionable en los tres detectores."
          />
          <DashMetricBlock
            label="Umbral de co-ocurrencia (bundle)"
            value={formatNumber(supuestos.umbral_co_ocurrencia_bundle)}
            icon={Boxes}
            tone="neutral"
            hint="Mínimo de veces que dos componentes deben aparecer juntos para proponer un bundle."
          />
        </div>

        <DashCard className="mt-6">
          <p className="text-[12px] uppercase tracking-[0.12em] text-dash-text-aux">Nota del backend</p>
          <p className="mt-2 text-[14px] leading-relaxed text-dash-text-muted">{supuestos.nota}</p>
        </DashCard>
      </DashSection>
    </>
  );
}
