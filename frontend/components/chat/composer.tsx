"use client";

import * as React from "react";
import { ArrowRight, Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";

import type { ChatTone } from "./types";

interface ComposerProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  busy?: boolean;
  placeholder?: string;
  tone?: ChatTone;
  autoFocus?: boolean;
  className?: string;
  ariaLabel?: string;
}

const MAX_HEIGHT_PX = 168;

/**
 * Una sola cápsula muy redondeada: textarea a la izquierda y círculo azul de
 * envío DENTRO del mismo rectángulo (§3.5). Enter envía, Shift+Enter salta línea.
 */
export function Composer({
  value,
  onChange,
  onSubmit,
  disabled = false,
  busy = false,
  placeholder = "Describe tu necesidad: potencia, tensión, características y presupuesto…",
  tone = "light",
  autoFocus = false,
  className,
  ariaLabel = "Mensaje para el asesor",
}: ComposerProps) {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);
  const light = tone === "light";

  React.useEffect(() => {
    const node = textareaRef.current;
    if (!node) return;
    node.style.height = "auto";
    node.style.height = `${Math.min(node.scrollHeight, MAX_HEIGHT_PX)}px`;
  }, [value]);

  const canSend = value.trim().length > 0 && !disabled && !busy;

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (canSend) onSubmit();
    }
  }

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        if (canSend) onSubmit();
      }}
      className={cn(
        "flex w-full items-end gap-3 rounded-[2rem] border p-2.5 pl-5 transition-shadow duration-200",
        light
          ? "border-chat-assistant-border bg-white shadow-[var(--elev-card-light)]"
          : "border-dash-border bg-dash-surface shadow-[var(--elev-2)]",
        className,
      )}
    >
      <textarea
        ref={textareaRef}
        rows={1}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        aria-label={ariaLabel}
        autoFocus={autoFocus}
        disabled={disabled}
        className={cn(
          "min-h-10 flex-1 resize-none self-center bg-transparent py-2 text-[15px] leading-relaxed outline-none scroll-slim",
          light
            ? "scroll-slim-light text-chat-text placeholder:text-chat-text-muted"
            : "text-dash-text placeholder:text-dash-text-aux",
        )}
      />

      <button
        type="submit"
        disabled={!canSend}
        aria-label="Enviar mensaje"
        className={cn(
          "flex size-11 shrink-0 items-center justify-center rounded-full transition-[background-color,transform,opacity] duration-150 disabled:opacity-40",
          light
            ? "bg-chat-user text-chat-user-text hover:bg-brand-dark"
            : "bg-dash-accent text-navy-950 hover:brightness-110",
          canSend && "active:scale-95",
        )}
      >
        {busy ? (
          <Loader2 className="size-5 animate-spin" strokeWidth={2} />
        ) : (
          <ArrowRight className="size-5" strokeWidth={2} />
        )}
      </button>
    </form>
  );
}
