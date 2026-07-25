"use client";

import * as React from "react";
import { Loader2, PackageOpen, Scale, TrendingUp, Users } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import type { ObjectiveOption, ObjectivesResponse, SetObjectiveResponse } from "@/lib/api/types";
import { describeError, isAbort } from "@/lib/errors";
import { cn } from "@/lib/utils";

import { DashCard, DashCardSkeleton, DashError, DashSection, WeightBar } from "./dash-ui";

const ICONS: Record<string, React.ElementType> = {
  balanced: Scale,
  customer_value: Users,
  maximize_margin: TrendingUp,
  clear_inventory: PackageOpen,
};

const WEIGHT_LABELS: Record<string, string> = {
  cost: "Costo",
  efficiency: "Eficiencia",
  availability: "Disponibilidad",
  margin: "Margen",
};

interface ViewObjectiveProps {
  activo: string | undefined;
  onChanged: (response: SetObjectiveResponse) => void;
  onError: (message: string) => void;
}

export function ViewObjective({ activo, onChanged, onError }: ViewObjectiveProps) {
  const [data, setData] = React.useState<ObjectivesResponse | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [pendingKey, setPendingKey] = React.useState<string | null>(null);

  const load = React.useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    try {
      setData(await api.objectives(signal));
      setError(null);
    } catch (cause) {
      if (!isAbort(cause)) setError(describeError(cause));
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  async function select(option: ObjectiveOption) {
    if (pendingKey) return;
    setPendingKey(option.clave);
    try {
      const response = await api.setObjective(option.clave);
      onChanged(response);
      setData((current) => (current ? { ...current, activo: response.activo } : current));
    } catch (cause) {
      onError(describeError(cause));
    } finally {
      setPendingKey(null);
    }
  }

  const activeKey = activo ?? data?.activo;

  if (!data && loading) {
    return (
      <DashSection title="Objetivo de negocio" subtitle="Cargando objetivos disponibles…">
        <div className="grid gap-6 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, index) => (
            <DashCardSkeleton key={index} lines={4} />
          ))}
        </div>
      </DashSection>
    );
  }

  if (!data) {
    return (
      <DashSection title="Objetivo de negocio">
        <DashError message={error ?? "Sin objetivos."} onRetry={() => void load()} />
      </DashSection>
    );
  }

  return (
    <DashSection title="Objetivo de negocio" subtitle={data.garantia}>
      {error ? (
        <div className="mb-6">
          <DashError message={error} onRetry={() => void load()} />
        </div>
      ) : null}

      <div className="grid gap-6 md:grid-cols-2">
        {data.disponibles.map((option) => {
          const Icon = ICONS[option.clave] ?? Scale;
          const active = option.clave === activeKey;
          const busy = pendingKey === option.clave;
          const weights = Object.entries(option.pesos) as [string, number][];

          return (
            <DashCard
              key={option.clave}
              interactive
              className={cn(
                "cursor-pointer",
                active && "border-dash-accent bg-[color-mix(in_oklab,var(--dash-surface),var(--dash-accent)_7%)]",
              )}
              role="button"
              tabIndex={0}
              aria-pressed={active}
              onClick={() => void select(option)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  void select(option);
                }
              }}
            >
              <div className="flex items-start justify-between gap-4">
                <span
                  className={cn(
                    "flex size-11 shrink-0 items-center justify-center rounded-full",
                    active
                      ? "bg-[var(--dash-accent-soft)] text-dash-accent"
                      : "bg-dash-surface-2 text-dash-text-muted",
                  )}
                >
                  <Icon className="size-[22px]" strokeWidth={1.75} />
                </span>

                {busy ? (
                  <Loader2 className="size-4 animate-spin text-dash-accent" strokeWidth={2} />
                ) : active ? (
                  <Badge tone="accent">Seleccionado</Badge>
                ) : null}
              </div>

              <h3 className="mt-5 text-[19px] font-medium leading-snug text-dash-text">
                {option.etiqueta}
              </h3>

              <dl className="mt-5 space-y-3">
                {weights.map(([dimension, weight]) => (
                  <div key={dimension}>
                    <div className="flex items-baseline justify-between gap-3">
                      <dt className="text-[13px] text-dash-text-muted">
                        {WEIGHT_LABELS[dimension] ?? dimension}
                      </dt>
                      <dd className="tnum font-mono text-[13px] text-dash-text">
                        {weight.toFixed(2)}
                      </dd>
                    </div>
                    <div className="mt-1.5">
                      <WeightBar value={weight} />
                    </div>
                  </div>
                ))}
              </dl>
            </DashCard>
          );
        })}
      </div>
    </DashSection>
  );
}
