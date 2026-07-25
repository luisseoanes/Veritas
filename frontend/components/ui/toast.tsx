"use client";

import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, CheckCircle2, Info, X } from "lucide-react";

import { cn } from "@/lib/utils";

type ToastTone = "ok" | "warn" | "danger" | "info";

interface Toast {
  id: number;
  title: string;
  description?: string;
  tone: ToastTone;
}

interface ToastContextValue {
  toast: (input: { title: string; description?: string; tone?: ToastTone }) => void;
}

const ToastContext = React.createContext<ToastContextValue | null>(null);

const ICONS: Record<ToastTone, React.ElementType> = {
  ok: CheckCircle2,
  warn: AlertTriangle,
  danger: AlertTriangle,
  info: Info,
};

const TONE_CLASS: Record<ToastTone, string> = {
  ok: "border-[color-mix(in_oklab,var(--dash-ok),transparent_50%)] text-dash-ok",
  warn: "border-[color-mix(in_oklab,var(--dash-warn),transparent_50%)] text-dash-warn",
  danger: "border-[color-mix(in_oklab,var(--dash-danger),transparent_50%)] text-dash-danger",
  info: "border-[color-mix(in_oklab,var(--dash-accent),transparent_50%)] text-dash-accent",
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<Toast[]>([]);
  const nextId = React.useRef(1);

  const dismiss = React.useCallback((id: number) => {
    setToasts((current) => current.filter((item) => item.id !== id));
  }, []);

  const toast = React.useCallback<ToastContextValue["toast"]>(
    ({ title, description, tone = "info" }) => {
      const id = nextId.current++;
      setToasts((current) => [...current, { id, title, description, tone }]);
      window.setTimeout(() => dismiss(id), 5200);
    },
    [dismiss],
  );

  const value = React.useMemo(() => ({ toast }), [toast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        className="pointer-events-none fixed bottom-6 right-6 z-50 flex w-[min(380px,calc(100vw-48px))] flex-col gap-3"
        role="status"
        aria-live="polite"
      >
        <AnimatePresence initial={false}>
          {toasts.map((item) => {
            const Icon = ICONS[item.tone];
            return (
              <motion.div
                key={item.id}
                layout
                initial={{ opacity: 0, y: 16, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8, scale: 0.98 }}
                transition={{ duration: 0.2, ease: "easeOut" }}
                className={cn(
                  "pointer-events-auto flex items-start gap-3 rounded-[var(--radius-card)] border bg-dash-surface p-4 shadow-[var(--elev-3)]",
                  TONE_CLASS[item.tone],
                )}
              >
                <Icon className="mt-0.5 size-[18px] shrink-0" strokeWidth={1.75} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-dash-text">{item.title}</p>
                  {item.description ? (
                    <p className="mt-1 text-[13px] leading-relaxed text-dash-text-muted">
                      {item.description}
                    </p>
                  ) : null}
                </div>
                <button
                  type="button"
                  onClick={() => dismiss(item.id)}
                  aria-label="Cerrar aviso"
                  className="rounded-full p-1 text-dash-text-aux transition-colors hover:text-dash-text"
                >
                  <X className="size-4" strokeWidth={1.75} />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const context = React.useContext(ToastContext);
  if (!context) throw new Error("useToast debe usarse dentro de <ToastProvider>.");
  return context;
}
