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
    <div className="dash-atmosphere flex h-dvh text-dash-text">
      <aside className="dash-glass relative z-10 hidden w-[220px] shrink-0 flex-col md:flex">
        <div className="relative flex h-14 shrink-0 items-center bg-navy-950 px-5">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 bg-[var(--banner-bg)] backdrop-blur-xl"
          />
          <Logo width={68} height={48} className="relative z-10 max-h-8 w-auto brightness-0 invert" />
        </div>

        <div className="flex min-h-0 flex-1 flex-col border-r border-[color-mix(in_oklab,var(--weg-blue)_12%,transparent)]">
          <nav className="flex flex-1 flex-col gap-0.5 px-2.5 py-1">
            <p className="mb-1.5 px-2.5 text-[11px] font-medium text-dash-text-aux">Menú</p>
            {ADMIN_VIEWS.map((item) => {
              const active = item.key === view;
              return (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => onViewChange(item.key)}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "group flex items-center gap-2.5 rounded-[var(--radius-control)] px-2.5 py-2 text-left text-[13px] font-medium transition-colors duration-150",
                    active
                      ? "bg-white text-dash-accent shadow-[var(--elev-1)]"
                      : "text-dash-text-muted hover:bg-white/70 hover:text-dash-text",
                  )}
                >
                  <item.icon
                    className={cn(
                      "size-4 shrink-0",
                      active ? "text-dash-accent" : "text-dash-text-aux group-hover:text-dash-text-muted",
                    )}
                    strokeWidth={1.75}
                  />
                  {item.label}
                </button>
              );
            })}
          </nav>

          <div className="border-t border-[color-mix(in_oklab,var(--weg-blue)_12%,transparent)] p-2.5">
            <Button variant="quiet" size="sm" onClick={onLogout} className="w-full justify-start gap-2.5 px-2.5">
              <LogOut className="size-4" strokeWidth={1.75} />
              Salir
            </Button>
          </div>
        </div>
      </aside>

      <div className="relative flex min-w-0 flex-1 flex-col">
        <header className="relative flex h-14 shrink-0 items-center gap-3 border-b border-[var(--banner-border)] bg-navy-950 px-5 lg:px-8">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 bg-[var(--banner-bg)] backdrop-blur-xl"
          />
          <Badge tone="onDark" size="md" className="relative z-10 gap-1.5">
            <Target className="size-3.5" strokeWidth={1.75} />
            {objectiveLabel(objetivoActivo)}
          </Badge>

          <div className="relative z-10 ml-auto flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={onReset} disabled={resetting}>
              <RotateCcw className={cn("size-3.5", resetting && "animate-spin")} strokeWidth={1.75} />
              Reset demo
            </Button>
            <Link href="/" className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}>
              <ArrowLeft className="size-3.5" strokeWidth={1.75} />
              Asesor
            </Link>
          </div>
        </header>

        <div className="flex gap-1.5 overflow-x-auto border-b border-dash-border bg-[var(--dash-sidebar)] px-4 py-2 md:hidden">
          {ADMIN_VIEWS.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => onViewChange(item.key)}
              className={cn(
                "flex shrink-0 items-center gap-1.5 rounded-[var(--radius-control)] px-2.5 py-1.5 text-[12px] font-medium",
                item.key === view
                  ? "bg-white text-dash-accent shadow-[var(--elev-1)]"
                  : "text-dash-text-muted hover:bg-white/70",
              )}
            >
              <item.icon className="size-3.5" strokeWidth={1.75} />
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

export function AdminContent({ children }: { children: React.ReactNode }) {
  return <div className="mx-auto w-full max-w-[1120px] px-5 py-8 lg:px-8">{children}</div>;
}
