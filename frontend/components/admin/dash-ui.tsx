"use client";

import * as React from "react";
import { AlertTriangle, Inbox, RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

/* ==========================================================================
   Primitivas del dashboard. Un solo lenguaje de card, una sola escala de
   espaciado y tipografía: si algo se ve distinto es porque significa distinto.
   ========================================================================== */

export function DashCard({
  className,
  interactive = false,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { interactive?: boolean }) {
  return (
    <div
      className={cn("dash-card", interactive && "dash-card-interactive", className)}
      {...props}
    />
  );
}

export function DashSection({
  title,
  subtitle,
  actions,
  children,
  className,
}: {
  title: string;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("mb-12 last:mb-0", className)}>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-[22px] font-medium leading-tight text-dash-text">{title}</h2>
          {subtitle ? (
            <p className="mt-1.5 max-w-2xl text-[13px] leading-relaxed text-dash-text-muted">
              {subtitle}
            </p>
          ) : null}
        </div>
        {actions ? <div className="flex items-center gap-3">{actions}</div> : null}
      </div>
      {children}
    </section>
  );
}

type MetricTone = "neutral" | "accent" | "ok" | "warn" | "danger";
type MetricSize = "hero" | "large" | "base";

const METRIC_TONE: Record<MetricTone, string> = {
  neutral: "text-dash-text",
  accent: "text-dash-accent",
  ok: "text-dash-ok",
  warn: "text-dash-warn",
  danger: "text-dash-danger",
};

const METRIC_ICON_TONE: Record<MetricTone, string> = {
  neutral: "bg-dash-surface-2 text-dash-text-muted",
  accent: "bg-[var(--dash-accent-soft)] text-dash-accent",
  ok: "bg-[var(--dash-ok-soft)] text-dash-ok",
  warn: "bg-[var(--dash-warn-soft)] text-dash-warn",
  danger: "bg-[var(--dash-danger-soft)] text-dash-danger",
};

const METRIC_SIZE: Record<MetricSize, string> = {
  hero: "text-[clamp(2.75rem,5.5vw,4.25rem)] leading-[0.95]",
  large: "text-[clamp(2rem,3vw,2.5rem)] leading-[1]",
  base: "text-[26px] leading-[1.1]",
};

export function DashMetricBlock({
  label,
  value,
  icon: Icon,
  tone = "neutral",
  size = "large",
  hint,
  loading = false,
  className,
}: {
  label: string;
  value: React.ReactNode;
  icon?: React.ElementType;
  tone?: MetricTone;
  size?: MetricSize;
  hint?: React.ReactNode;
  loading?: boolean;
  className?: string;
}) {
  return (
    <DashCard className={cn("flex flex-col justify-between gap-6", className)}>
      <div className="flex items-start justify-between gap-4">
        <p className="text-[13px] font-medium uppercase tracking-[0.12em] text-dash-text-muted">
          {label}
        </p>
        {Icon ? (
          <span
            className={cn(
              "flex size-10 shrink-0 items-center justify-center rounded-full",
              METRIC_ICON_TONE[tone],
            )}
          >
            <Icon className="size-5" strokeWidth={1.75} />
          </span>
        ) : null}
      </div>

      <div>
        {loading ? (
          <Skeleton className="h-12 w-40" />
        ) : (
          <p className={cn("tnum font-medium", METRIC_SIZE[size], METRIC_TONE[tone])}>{value}</p>
        )}
        {hint ? (
          <p className="mt-3 text-[13px] leading-relaxed text-dash-text-muted">{hint}</p>
        ) : null}
      </div>
    </DashCard>
  );
}

export function DashKeyValue({
  label,
  value,
  tone = "neutral",
  mono = false,
}: {
  label: string;
  value: React.ReactNode;
  tone?: MetricTone;
  mono?: boolean;
}) {
  return (
    <div>
      <p className="text-[12px] uppercase tracking-[0.1em] text-dash-text-aux">{label}</p>
      <p
        className={cn(
          "tnum mt-1 text-[15px] font-medium",
          METRIC_TONE[tone],
          mono && "font-mono text-[14px]",
        )}
      >
        {value}
      </p>
    </div>
  );
}

/** La fórmula del detector siempre visible, nunca en tooltip (§3.7). */
export function FormulaBlock({ formula, label = "Fórmula" }: { formula: string; label?: string }) {
  return (
    <div className="rounded-[var(--radius-control)] border border-dash-border bg-dash-bg p-3">
      <p className="mb-1.5 font-mono text-[11px] uppercase tracking-[0.12em] text-dash-text-aux">
        {label}
      </p>
      <p className="font-mono text-[13px] leading-relaxed break-words text-dash-text">{formula}</p>
    </div>
  );
}

export function RecommendationBlock({ text }: { text: string }) {
  return (
    <div className="rounded-[var(--radius-control)] border border-[color-mix(in_oklab,var(--dash-accent),transparent_70%)] bg-[var(--dash-accent-soft)] p-3">
      <p className="mb-1.5 text-[11px] font-medium uppercase tracking-[0.12em] text-dash-accent">
        Recomendación
      </p>
      <p className="text-[13px] leading-relaxed text-dash-text">{text}</p>
    </div>
  );
}

export function DashEmpty({ message }: { message: string }) {
  return (
    <DashCard className="flex items-center gap-4">
      <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-dash-surface-2 text-dash-text-aux">
        <Inbox className="size-5" strokeWidth={1.75} />
      </span>
      <p className="text-[14px] text-dash-text-muted">{message}</p>
    </DashCard>
  );
}

export function DashError({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <DashCard className="border-[color-mix(in_oklab,var(--dash-danger),transparent_60%)]">
      <div className="flex items-start gap-4">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-[var(--dash-danger-soft)] text-dash-danger">
          <AlertTriangle className="size-5" strokeWidth={1.75} />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-[15px] font-medium text-dash-text">No se pudo cargar</p>
          <p className="mt-1.5 text-[13px] leading-relaxed text-dash-text-muted">{message}</p>
          {onRetry ? (
            <Button variant="dash" size="sm" onClick={onRetry} className="mt-4">
              <RotateCcw className="size-3.5" strokeWidth={1.75} />
              Reintentar
            </Button>
          ) : null}
        </div>
      </div>
    </DashCard>
  );
}

export function DashCardSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <DashCard className="space-y-4">
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-10 w-44" />
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton key={index} className="h-3 w-full" />
      ))}
    </DashCard>
  );
}

/** Barra de peso de objetivo: sutil, sin gradientes ni sombras extra. */
export function WeightBar({ value }: { value: number }) {
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-dash-surface-2">
      <div
        className="h-full rounded-full bg-dash-accent transition-[width] duration-200"
        style={{ width: `${Math.max(0, Math.min(1, value)) * 100}%` }}
      />
    </div>
  );
}
