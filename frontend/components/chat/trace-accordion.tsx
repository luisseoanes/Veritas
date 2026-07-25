"use client";

import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, Cpu, Wrench } from "lucide-react";

import type { TraceStep } from "@/lib/api/types";
import { formatTime } from "@/lib/format";
import { cn } from "@/lib/utils";

import type { ChatTone } from "./types";

interface TraceAccordionProps {
  trace: TraceStep[];
  tone?: ChatTone;
}

/**
 * Panel de evidencia: qué tool llamó el agente, con qué argumentos y qué
 * devolvió. Es lo que prueba que la recomendación no está inventada.
 */
export function TraceAccordion({ trace, tone = "light" }: TraceAccordionProps) {
  const [open, setOpen] = React.useState(false);
  if (!trace?.length) return null;

  const light = tone === "light";

  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className={cn(
          "inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-[12px] font-medium transition-colors duration-150",
          light
            ? "border-chat-assistant-border bg-chat-trace text-chat-text-muted hover:text-chat-text"
            : "border-dash-border bg-dash-surface-2 text-dash-text-muted hover:text-dash-text",
        )}
      >
        <ChevronDown
          className={cn("size-3.5 transition-transform duration-200", open && "rotate-180")}
          strokeWidth={2}
        />
        Ver razonamiento
        <span className={cn("font-mono", light ? "text-chat-accent" : "text-dash-accent")}>
          {trace.length} {trace.length === 1 ? "paso" : "pasos"}
        </span>
      </button>

      <AnimatePresence initial={false}>
        {open ? (
          <motion.div
            key="trace"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.24, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <ol
              className={cn(
                "mt-3 space-y-3 rounded-[var(--radius-card)] border p-4",
                light
                  ? "border-chat-assistant-border bg-chat-trace"
                  : "border-dash-border bg-dash-surface-2",
              )}
            >
              {trace.map((step) => (
                <TraceStepRow key={`${step.step}-${step.timestamp}`} step={step} light={light} />
              ))}
            </ol>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}

function TraceStepRow({ step, light }: { step: TraceStep; light: boolean }) {
  const isTool = step.kind === "tool";
  const Icon = isTool ? Wrench : Cpu;
  const detail = step.detail ?? {};

  const toolName = typeof detail.name === "string" ? detail.name : null;
  const provider = typeof detail.provider === "string" ? detail.provider : null;
  const text = typeof detail.text === "string" ? detail.text : null;

  return (
    <li className="flex gap-3">
      <span
        className={cn(
          "mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full text-[11px] font-mono",
          light ? "bg-chat-user text-chat-user-text" : "bg-dash-accent text-navy-950",
        )}
      >
        {step.step}
      </span>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={cn(
              "inline-flex items-center gap-1.5 text-[12px] font-medium uppercase tracking-[0.1em]",
              light ? "text-chat-text-muted" : "text-dash-text-muted",
            )}
          >
            <Icon className="size-3.5" strokeWidth={1.75} />
            {step.kind}
          </span>
          {toolName ? (
            <code
              className={cn(
                "rounded-full px-2 py-0.5 font-mono text-[12px]",
                light ? "bg-white text-chat-accent" : "bg-dash-surface text-dash-accent",
              )}
            >
              {toolName}
            </code>
          ) : null}
          {provider ? (
            <span
              className={cn("font-mono text-[11px]", light ? "text-chat-text-muted" : "text-dash-text-aux")}
            >
              {provider}
            </span>
          ) : null}
          <span
            className={cn(
              "ml-auto font-mono text-[11px]",
              light ? "text-chat-text-muted" : "text-dash-text-aux",
            )}
          >
            {formatTime(step.timestamp)}
          </span>
        </div>

        {text ? (
          <p className={cn("mt-1.5 text-[13px] leading-relaxed", light ? "text-chat-text" : "text-dash-text")}>
            {text}
          </p>
        ) : null}

        {isTool ? (
          <div className="mt-2 space-y-2">
            <DetailBlock label="arguments" value={detail.arguments} light={light} />
            <DetailBlock label="result" value={detail.result} light={light} />
          </div>
        ) : (
          <DetailBlock label="tool_calls" value={detail.tool_calls} light={light} />
        )}
      </div>
    </li>
  );
}

function DetailBlock({
  label,
  value,
  light,
}: {
  label: string;
  value: unknown;
  light: boolean;
}) {
  if (value === undefined || value === null) return null;
  const rendered = pretty(value);
  if (!rendered.trim() || rendered === "{}" || rendered === "[]") return null;

  return (
    <div>
      <p
        className={cn(
          "mb-1 font-mono text-[11px] uppercase tracking-[0.1em]",
          light ? "text-chat-text-muted" : "text-dash-text-aux",
        )}
      >
        {label}
      </p>
      <pre
        className={cn(
          "max-h-56 overflow-auto scroll-slim rounded-[var(--radius-control)] border p-2.5 font-mono text-[12px] leading-relaxed whitespace-pre-wrap break-words",
          light
            ? "scroll-slim-light border-chat-assistant-border bg-white text-chat-text"
            : "border-dash-border bg-dash-bg text-dash-text-muted",
        )}
      >
        {rendered}
      </pre>
    </div>
  );
}

/** Los `result` de tools llegan como string JSON (a veces truncado): se intenta
 *  formatear y, si no parsea, se muestra el texto crudo sin ocultar nada. */
function pretty(value: unknown): string {
  if (typeof value === "string") {
    try {
      return JSON.stringify(JSON.parse(value), null, 2);
    } catch {
      return value;
    }
  }
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}
