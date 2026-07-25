"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowLeft, LogOut, RotateCcw, Target } from "lucide-react";

import { ADMIN_VIEWS, type AdminView } from "@/components/admin/views";
import { Logo } from "@/components/brand/logo";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { objectiveLabel } from "@/lib/demo";
import { cn } from "@/lib/utils";

interface AdminShellProps {
  view: AdminView;
  onViewChange: (view: AdminView) => void;
  objetivoActivo: string | undefined;
  onReset: () => void;
  resetting?: boolean;
  onLogout: () => void;
  /** `true` para vistas que manejan su propio scroll interno (chatbot). */
  fill?: boolean;
  children: React.ReactNode;
}

export function AdminShell({
  view,
  onViewChange,
  objetivoActivo,
  onReset,
  resetting = false,
  onLogout,
  fill = false,
  children,
}: AdminShellProps) {
  return (
    <div className="flex h-dvh bg-dash-bg text-dash-text">
      <aside className="hidden w-[220px] shrink-0 flex-col border-r border-dash-border bg-[color-mix(in_oklab,var(--dash-bg),black_18%)] md:flex">
        <div className="flex h-16 items-center px-6">
          <Logo width={72} height={50} className="max-h-10 w-auto" />
        </div>

        <nav className="flex flex-1 flex-col gap-1 px-3 py-4">
          {ADMIN_VIEWS.map((item) => {
            const active = item.key === view;
            return (
              <button
                key={item.key}
                type="button"
                onClick={() => onViewChange(item.key)}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center gap-3 rounded-[var(--radius-control)] px-3 py-2.5 text-left text-[14px] transition-colors duration-150",
                  active
                    ? "bg-[var(--dash-accent-soft)] text-dash-accent"
                    : "text-dash-text-muted hover:bg-dash-surface hover:text-dash-text",
                )}
              >
                <item.icon className="size-[18px] shrink-0" strokeWidth={1.75} />
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="border-t border-dash-border p-3">
          <Button variant="quiet" size="sm" onClick={onLogout} className="w-full justify-start gap-3 px-3">
            <LogOut className="size-[18px]" strokeWidth={1.75} />
            Salir
          </Button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center gap-4 border-b border-dash-border bg-[color-mix(in_oklab,var(--dash-bg),black_10%)] px-6">
          <Badge tone="accent" size="lg" className="gap-2">
            <Target className="size-3.5" strokeWidth={2} />
            Objetivo: {objectiveLabel(objetivoActivo)}
          </Badge>

          <div className="ml-auto flex items-center gap-3">
            <Button variant="dash" size="sm" onClick={onReset} disabled={resetting}>
              <RotateCcw className={cn("size-3.5", resetting && "animate-spin")} strokeWidth={1.75} />
              Reset demo
            </Button>
            <Link href="/" className={buttonVariants({ variant: "dash", size: "sm" })}>
              <ArrowLeft className="size-3.5" strokeWidth={1.75} />
              Volver al asesor
            </Link>
          </div>
        </header>

        {/* Nav móvil: el sidebar se colapsa a chips scrollables */}
        <div className="flex gap-2 overflow-x-auto border-b border-dash-border px-4 py-3 md:hidden">
          {ADMIN_VIEWS.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => onViewChange(item.key)}
              className={cn(
                "flex shrink-0 items-center gap-2 rounded-full border px-3 py-1.5 text-[13px]",
                item.key === view
                  ? "border-dash-accent bg-[var(--dash-accent-soft)] text-dash-accent"
                  : "border-dash-border text-dash-text-muted",
              )}
            >
              <item.icon className="size-4" strokeWidth={1.75} />
              {item.label}
            </button>
          ))}
        </div>

        <main
          className={cn(
            "min-h-0 flex-1",
            fill ? "overflow-hidden" : "overflow-y-auto scroll-slim",
          )}
        >
          {children}
        </main>
      </div>
    </div>
  );
}

/** Contenedor de contenido: max 1200px y márgenes laterales de 24–32px. */
export function AdminContent({ children }: { children: React.ReactNode }) {
  return <div className="mx-auto w-full max-w-[1200px] px-6 py-8 lg:px-8">{children}</div>;
}
