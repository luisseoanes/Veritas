"use client";

import * as React from "react";
import { AlertTriangle, Inbox, RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

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

/** Contenedor de composición (bento / stage). */
export function DashPanel({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("dash-panel", className)} {...props}>
      {children}
    </div>
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
        <div className="min-w-0">
          <h2 className="text-[15px] font-semibold tracking-tight text-dash-text">{title}</h2>
          {subtitle ? (
            <p className="mt-1 max-w-2xl text-[13px] leading-relaxed text-dash-text-muted">
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
type MetricSize = "hero" | "large" | "base" | "sm";

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
  hero: "text-[clamp(2.75rem,4.5vw,3.5rem)] font-semibold leading-none tracking-tight",
  large: "text-[2rem] font-semibold leading-none tracking-tight",
  base: "text-[1.5rem] font-semibold leading-none tracking-tight",
  sm: "text-[1.25rem] font-semibold leading-none tracking-tight",
};

/** Métrica inline: el número manda; la etiqueta es secundaria. */
export function DashCounter({
  label,
  value,
  tone = "neutral",
  size = "large",
  className,
}: {
  label: string;
  value: React.ReactNode;
  tone?: MetricTone;
  size?: MetricSize;
  className?: string;
}) {
  return (
    <div className={cn("dash-counter flex flex-col gap-2 px-5 py-4", className)}>
      <p className="text-[12px] font-medium text-dash-text-muted">{label}</p>
      <p className={cn("tnum", METRIC_SIZE[size], METRIC_TONE[tone])}>{value}</p>
    </div>
  );
}

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
      <div className="flex items-start justify-between gap-3">
        <p className="text-[12px] font-medium text-dash-text-muted">{label}</p>
        {Icon ? (
          <span
            className={cn(
              "flex size-8 shrink-0 items-center justify-center rounded-lg",
              METRIC_ICON_TONE[tone],
            )}
          >
            <Icon className="size-4" strokeWidth={1.75} />
          </span>
        ) : null}
      </div>

      <div>
        {loading ? (
          <Skeleton className="h-10 w-36" />
        ) : (
          <p className={cn("tnum", METRIC_SIZE[size], METRIC_TONE[tone])}>{value}</p>
        )}
        {hint ? (
          <p className="mt-2 text-[13px] leading-relaxed text-dash-text-aux">{hint}</p>
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
      <p className="text-[12px] font-medium text-dash-text-aux">{label}</p>
      <p
        className={cn(
          "tnum mt-1 text-[14px] font-semibold",
          METRIC_TONE[tone],
          mono && "font-mono text-[13px] font-medium",
        )}
      >
        {value}
      </p>
    </div>
  );
}

export function FormulaBlock({ formula, label = "Fórmula" }: { formula: string; label?: string }) {
  return (
    <div className="rounded-[var(--radius-control)] border border-dash-border bg-dash-surface-2 px-3.5 py-3">
      <p className="mb-1 text-[11px] font-medium text-dash-text-aux">{label}</p>
      <p className="font-mono text-[12px] leading-relaxed break-words text-dash-text-muted">
        {formula}
      </p>
    </div>
  );
}

export function RecommendationBlock({ text }: { text: string }) {
  return (
    <div className="rounded-[var(--radius-control)] border border-dash-border bg-[var(--dash-accent-soft)] px-3.5 py-3">
      <p className="mb-1 text-[11px] font-semibold text-dash-accent">Recomendación</p>
      <p className="text-[13px] leading-relaxed text-dash-text">{text}</p>
    </div>
  );
}

export function DashEmpty({ message }: { message: string }) {
  return (
    <DashCard className="flex items-center gap-3.5 py-5">
      <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-dash-surface-2 text-dash-text-aux">
        <Inbox className="size-4" strokeWidth={1.75} />
      </span>
      <p className="text-[13px] text-dash-text-muted">{message}</p>
    </DashCard>
  );
}

export function DashError({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <DashCard>
      <div className="flex items-start gap-3.5">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-[var(--dash-danger-soft)] text-dash-danger">
          <AlertTriangle className="size-4" strokeWidth={1.75} />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-[14px] font-semibold text-dash-text">No se pudo cargar</p>
          <p className="mt-1 text-[13px] leading-relaxed text-dash-text-muted">{message}</p>
          {onRetry ? (
            <Button variant="dash" size="sm" onClick={onRetry} className="mt-3">
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
    <DashCard className="space-y-3">
      <Skeleton className="h-3.5 w-28" />
      <Skeleton className="h-9 w-40" />
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton key={index} className="h-3 w-full" />
      ))}
    </DashCard>
  );
}

export function WeightBar({ value }: { value: number }) {
  return (
    <div className="dash-bar-track">
      <div
        className="dash-bar-fill transition-[width] duration-300"
        style={{ width: `${Math.max(0, Math.min(1, value)) * 100}%` }}
      />
    </div>
  );
}
