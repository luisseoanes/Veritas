"use client";

import { Boxes, PackageSearch, TriangleAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { BundleGap, DashboardResponse, InventoryRisk, UnmetDemand } from "@/lib/api/types";
import { formatCop, formatNumber, humanizeConstraint } from "@/lib/format";

import {
  DashCard,
  DashCardSkeleton,
  DashEmpty,
  DashError,
  DashKeyValue,
  DashSection,
  FormulaBlock,
  RecommendationBlock,
} from "./dash-ui";

interface ViewOpportunitiesProps {
  data: DashboardResponse | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

export function ViewOpportunities({ data, loading, error, onRetry }: ViewOpportunitiesProps) {
  if (!data && loading) {
    return (
      <DashSection title="Oportunidades" subtitle="Cargando detectores…">
        <div className="grid gap-6 lg:grid-cols-2">
          <DashCardSkeleton lines={5} />
          <DashCardSkeleton lines={5} />
        </div>
      </DashSection>
    );
  }

  if (!data) {
    return (
      <DashSection title="Oportunidades">
        <DashError message={error ?? "Sin datos del dashboard."} onRetry={onRetry} />
      </DashSection>
    );
  }

  return (
    <>
      <DashSection
        title="Demanda no satisfecha"
        subtitle="Conversaciones que el solver no pudo resolver, agrupadas por la restricción que las hizo imposibles."
      >
        {data.demanda_no_satisfecha.length ? (
          <div className="grid gap-6 lg:grid-cols-2">
            {data.demanda_no_satisfecha.map((item, index) => (
              <UnmetDemandCard key={`${item.tipo}-${index}`} item={item} />
            ))}
          </div>
        ) : (
          <DashEmpty message="Ninguna brecha de demanda detectada sobre los eventos acumulados." />
        )}
      </DashSection>

      <DashSection
        title="Brechas de bundle"
        subtitle="Componentes que el solver combina una y otra vez y que hoy se cotizan por separado."
      >
        {data.brechas_de_bundle.length ? (
          <div className="grid gap-6 lg:grid-cols-2">
            {data.brechas_de_bundle.map((item, index) => (
              <BundleGapCard key={`${item.componentes.join("-")}-${index}`} item={item} />
            ))}
          </div>
        ) : (
          <DashEmpty message="Ninguna co-ocurrencia supera el umbral declarado." />
        )}
      </DashSection>

      <DashSection
        title="Riesgo de inventario"
        subtitle="Componentes cuya falta dejaría configuraciones sin alternativa válida."
      >
        {data.riesgo_de_inventario.length ? (
          <div className="grid gap-6 lg:grid-cols-2">
            {data.riesgo_de_inventario.map((item, index) => (
              <InventoryRiskCard key={`${item.componente}-${index}`} item={item} />
            ))}
          </div>
        ) : (
          <DashEmpty message="Sin componentes en riesgo con el stock actual." />
        )}
      </DashSection>
    </>
  );
}

function UnmetDemandCard({ item }: { item: UnmetDemand }) {
  const priceGap = item.naturaleza === "brecha_de_precio";
  return (
    <DashCard interactive className="flex flex-col gap-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-[var(--dash-danger-soft)] text-dash-danger">
            <PackageSearch className="size-5" strokeWidth={1.75} />
          </span>
          <div>
            <p className="text-[17px] font-medium leading-tight text-dash-text">
              {formatNumber(item.clientes_afectados)} clientes afectados
            </p>
            <p className="mt-0.5 text-[13px] text-dash-text-muted">
              {item.perfil.power_kw !== undefined ? `${item.perfil.power_kw} kW` : "—"}
              {item.perfil.voltage !== undefined ? ` · ${item.perfil.voltage} V` : ""}
            </p>
          </div>
        </div>
        <Badge tone={priceGap ? "warn" : "danger"}>{humanizeConstraint(item.naturaleza)}</Badge>
      </div>

      <div className="grid grid-cols-2 gap-5">
        <DashKeyValue label="Presupuesto promedio" value={formatCop(item.presupuesto_promedio_cop)} />
        <DashKeyValue label="Mínimo viable" value={formatCop(item.minimo_viable_cop)} />
        <DashKeyValue label="Brecha" value={formatCop(item.brecha_cop)} tone="danger" />
        <DashKeyValue
          label="Demanda direccionable"
          value={formatCop(item.demanda_direccionable_cop)}
          tone="accent"
        />
      </div>

      <div>
        <p className="mb-2 text-[12px] uppercase tracking-[0.1em] text-dash-text-aux">
          Restricción causante
        </p>
        <div className="flex flex-wrap gap-2">
          {item.restriccion_causante.map((constraint) => (
            <Badge key={constraint} size="sm" className="font-mono">
              {humanizeConstraint(constraint)}
            </Badge>
          ))}
        </div>
      </div>

      <FormulaBlock formula={item.formula} />
      <RecommendationBlock text={item.recomendacion} />
    </DashCard>
  );
}

function BundleGapCard({ item }: { item: BundleGap }) {
  return (
    <DashCard interactive className="flex flex-col gap-5">
      <div className="flex items-start gap-3">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-[var(--dash-accent-soft)] text-dash-accent">
          <Boxes className="size-5" strokeWidth={1.75} />
        </span>
        <div className="min-w-0">
          <p className="text-[17px] font-medium leading-snug text-dash-text">
            {item.nombres.join(" + ")}
          </p>
          <p className="mt-1 font-mono text-[12px] text-dash-text-aux">
            {item.componentes.join(" · ")}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-5">
        <DashKeyValue label="Co-ocurrencias" value={formatNumber(item.co_ocurrencias)} />
        <DashKeyValue label="Margen combinado" value={formatCop(item.margen_combinado_cop)} />
        <DashKeyValue
          label="Impacto estimado"
          value={formatCop(item.impacto_estimado_cop)}
          tone="accent"
        />
      </div>

      <FormulaBlock formula={item.formula} />
      <RecommendationBlock text={item.recomendacion} />
    </DashCard>
  );
}

function InventoryRiskCard({ item }: { item: InventoryRisk }) {
  const severe = item.indice_riesgo >= 10;
  return (
    <DashCard interactive className="flex flex-col gap-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span
            className={`flex size-10 shrink-0 items-center justify-center rounded-full ${
              severe
                ? "bg-[var(--dash-danger-soft)] text-dash-danger"
                : "bg-[var(--dash-warn-soft)] text-dash-warn"
            }`}
          >
            <TriangleAlert className="size-5" strokeWidth={1.75} />
          </span>
          <div className="min-w-0">
            <p className="text-[17px] font-medium leading-snug text-dash-text">{item.nombre}</p>
            <p className="mt-1 font-mono text-[12px] text-dash-text-aux">{item.componente}</p>
          </div>
        </div>
        <Badge tone={severe ? "danger" : "warn"} className="tnum">
          Índice {formatNumber(item.indice_riesgo, 1)}
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-5 sm:grid-cols-4">
        <DashKeyValue label="Stock" value={formatNumber(item.stock)} tone={severe ? "danger" : "warn"} />
        <DashKeyValue label="Única opción para" value={formatNumber(item.unica_opcion_para)} />
        <DashKeyValue label="Veces recomendado" value={formatNumber(item.veces_recomendado)} />
        <DashKeyValue label="Exposición" value={formatCop(item.exposicion_cop)} tone="accent" />
      </div>

      <FormulaBlock formula={item.formula} />
      <RecommendationBlock text={item.recomendacion} />
    </DashCard>
  );
}
