"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertTriangle, ArrowLeft, KeyRound, Loader2, ShieldCheck } from "lucide-react";

import { BRAND } from "@/lib/demo";
import { api, ApiError } from "@/lib/api";
import { clearAdminToken, setAdminToken } from "@/lib/admin-token";
import { ADMIN_TOKEN_HINT } from "@/lib/env";
import { describeError } from "@/lib/errors";

export default function AdminLoginPage() {
  return (
    <div className="relative flex min-h-dvh flex-col overflow-hidden bg-navy-950">
      <div
        className="pointer-events-none absolute inset-0"
        style={{ background: "var(--login-veil)" }}
        aria-hidden
      />
      <div className="relative flex min-h-dvh items-center justify-center px-5 py-12">
        <React.Suspense fallback={null}>
          <LoginCard />
        </React.Suspense>
      </div>
    </div>
  );
}

/** Logo pequeño azul solo en login (máscara + `--weg-blue`). */
function LoginBrandMark() {
  return (
    <Link
      href="/"
      aria-label="Ir al inicio"
      className="block h-7 w-10 shrink-0 bg-brand transition-opacity duration-150 hover:opacity-85"
      style={{
        WebkitMaskImage: `url(${BRAND.logoSrc})`,
        maskImage: `url(${BRAND.logoSrc})`,
        WebkitMaskRepeat: "no-repeat",
        maskRepeat: "no-repeat",
        WebkitMaskSize: "contain",
        maskSize: "contain",
        WebkitMaskPosition: "left center",
        maskPosition: "left center",
      }}
    />
  );
}

function LoginCard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const expired = searchParams.get("expirado") === "1";

  const [token, setToken] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [submitting, setSubmitting] = React.useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const value = token.trim();
    if (!value || submitting) return;

    setSubmitting(true);
    setError(null);
    setAdminToken(value);

    try {
      const response = await api.verifyAdmin();
      if (!response.ok) throw new ApiError(401, "El backend no confirmó el token.");
      router.replace("/admin");
    } catch (cause) {
      clearAdminToken();
      setError(
        cause instanceof ApiError && cause.isServerMisconfigured
          ? "El servidor no tiene ADMIN_TOKEN configurado: es un problema del backend, no del token."
          : describeError(cause),
      );
      setSubmitting(false);
    }
  }

  return (
    <div className="w-full max-w-[420px]">
      <div className="rounded-3xl bg-white p-8 shadow-[var(--elev-3)]">
        <div className="flex items-start justify-start">
          <LoginBrandMark />
        </div>

        <h1 className="mt-6 text-[26px] font-medium leading-tight text-chat-text">Acceso admin</h1>
        <p className="mt-2 text-[14px] leading-relaxed text-chat-text-muted">
          Un solo token compartido, sin usuarios. Se valida contra{" "}
          <code className="font-mono text-[13px] text-chat-accent">GET /admin/verify</code> antes de
          entrar al panel.
        </p>

        {expired ? (
          <p className="mt-5 flex items-start gap-2 rounded-[var(--radius-control)] border border-[var(--chat-danger-border)] bg-[var(--chat-danger-bg)] p-3 text-[13px] leading-relaxed text-[var(--chat-danger-text)]">
            <AlertTriangle className="mt-0.5 size-4 shrink-0" strokeWidth={1.75} />
            La sesión de administrador expiró o el token dejó de ser válido. Vuelve a ingresarlo.
          </p>
        ) : null}

        <form onSubmit={handleSubmit} className="mt-7">
          <label htmlFor="admin-token" className="block text-[13px] font-medium text-chat-text">
            Token de administrador
          </label>
          <div className="mt-2 flex items-center gap-2 rounded-full border border-chat-assistant-border bg-chat-stage-soft px-4 focus-within:border-chat-accent">
            <KeyRound className="size-4 shrink-0 text-chat-text-muted" strokeWidth={1.75} />
            <input
              id="admin-token"
              type="password"
              value={token}
              onChange={(event) => setToken(event.target.value)}
              placeholder={ADMIN_TOKEN_HINT || "Pega aquí el token"}
              autoComplete="off"
              autoFocus
              className="h-12 flex-1 bg-transparent font-mono text-[14px] text-chat-text outline-none placeholder:font-sans placeholder:text-chat-text-muted"
            />
          </div>

          {error ? (
            <p className="mt-3 flex items-start gap-2 text-[13px] leading-relaxed text-[var(--chat-danger-text)]">
              <AlertTriangle className="mt-0.5 size-4 shrink-0" strokeWidth={1.75} />
              {error}
            </p>
          ) : null}

          <button
            type="submit"
            disabled={submitting || token.trim().length === 0}
            className="mt-6 flex h-12 w-full items-center justify-center gap-2 rounded-full bg-chat-user text-[15px] font-medium text-chat-user-text transition-colors duration-150 hover:bg-brand-dark disabled:opacity-40"
          >
            {submitting ? (
              <Loader2 className="size-4 animate-spin" strokeWidth={2} />
            ) : (
              <ShieldCheck className="size-4" strokeWidth={2} />
            )}
            Entrar al panel
          </button>
        </form>

        <Link
          href="/"
          className="mt-6 inline-flex items-center gap-2 text-[13px] text-chat-text-muted transition-colors hover:text-chat-accent"
        >
          <ArrowLeft className="size-4" strokeWidth={1.75} />
          Volver al asesor
        </Link>
      </div>
    </div>
  );
}
