"use client";

import { motion } from "framer-motion";
import { AlertTriangle, FlaskConical, RotateCcw } from "lucide-react";

import { cn } from "@/lib/utils";

import { TraceAccordion } from "./trace-accordion";
import type { ChatMessage, ChatTone } from "./types";
import { WordStream } from "./word-stream";

interface MessageBubbleProps {
  message: ChatMessage;
  tone?: ChatTone;
  onTick?: () => void;
  onStreamDone?: (id: string) => void;
  onRetry?: () => void;
}

export function MessageBubble({
  message,
  tone = "light",
  onTick,
  onStreamDone,
  onRetry,
}: MessageBubbleProps) {
  const light = tone === "light";

  if (message.role === "user") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        className="flex justify-end"
      >
        <div
          className={cn(
            "max-w-[85%] rounded-[1.5rem] px-5 py-3 text-[15px] leading-relaxed whitespace-pre-wrap",
            light ? "bg-chat-user text-chat-user-text" : "bg-brand text-ice",
          )}
        >
          {message.content}
        </div>
      </motion.div>
    );
  }

  if (message.status === "loading") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        className="flex justify-start"
      >
        <div
          className={cn(
            "inline-flex items-center gap-3 rounded-[1.5rem] px-5 py-3 text-[14px]",
            light ? "bg-chat-loading text-chat-text-muted" : "bg-dash-surface-2 text-dash-text-muted",
          )}
        >
          <span className="flex gap-1">
            {[0, 1, 2].map((index) => (
              <motion.span
                key={index}
                className={cn(
                  "size-1.5 rounded-full",
                  light ? "bg-chat-accent" : "bg-dash-accent",
                )}
                animate={{ opacity: [0.25, 1, 0.25] }}
                transition={{ duration: 1.1, repeat: Infinity, delay: index * 0.16 }}
              />
            ))}
          </span>
          Resolviendo restricciones…
        </div>
      </motion.div>
    );
  }

  if (message.status === "error") {
    return (
      <div className="flex justify-start">
        <div
          className={cn(
            "max-w-[85%] rounded-[1.5rem] border px-5 py-3 text-[14px] leading-relaxed",
            light
              ? "border-[var(--chat-danger-border)] bg-[var(--chat-danger-bg)] text-[var(--chat-danger-text)]"
              : "border-[color-mix(in_oklab,var(--dash-danger),transparent_55%)] bg-[var(--dash-danger-soft)] text-dash-danger",
          )}
        >
          <p className="flex items-start gap-2">
            <AlertTriangle className="mt-0.5 size-4 shrink-0" strokeWidth={1.75} />
            <span>{message.content}</span>
          </p>
          {onRetry ? (
            <button
              type="button"
              onClick={onRetry}
              className="mt-3 inline-flex items-center gap-2 rounded-full border border-current px-3 py-1.5 text-[12px] font-medium transition-opacity hover:opacity-80"
            >
              <RotateCcw className="size-3.5" strokeWidth={1.75} />
              Reintentar
            </button>
          ) : null}
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className="flex justify-start"
    >
      <div
        className={cn(
          "max-w-[92%] rounded-[1.5rem] border px-5 py-4",
          light
            ? "border-chat-assistant-border bg-chat-assistant text-chat-assistant-text"
            : "border-dash-border bg-dash-surface text-dash-text",
        )}
      >
        {message.simulado ? (
          <p
            className={cn(
              "mb-2 inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium uppercase tracking-[0.1em]",
              light
                ? "bg-chat-trace text-chat-text-muted"
                : "bg-[var(--dash-warn-soft)] text-dash-warn",
            )}
          >
            <FlaskConical className="size-3.5" strokeWidth={1.75} />
            Respuesta simulada
          </p>
        ) : null}

        <p className="text-[15px] leading-relaxed whitespace-pre-wrap">
          <WordStream
            text={message.content}
            animate={message.status === "streaming"}
            onTick={onTick}
            onDone={() => onStreamDone?.(message.id)}
          />
        </p>

        <TraceAccordion trace={message.trace ?? []} tone={tone} />
      </div>
    </motion.div>
  );
}
