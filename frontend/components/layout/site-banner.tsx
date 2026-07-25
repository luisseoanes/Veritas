import Link from "next/link";
import { ShieldCheck } from "lucide-react";

import { Logo } from "@/components/brand/logo";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/**
 * Banner del cliente. Solo logo + acceso admin: sin nombre de producto, sin
 * badge de marca, sin objetivo activo y sin toggle de mocks (§3.7).
 */
export function SiteBanner() {
  return (
    <header className="shrink-0 border-b border-[var(--banner-border)] bg-[var(--banner-bg)] backdrop-blur-xl">
      <div className="flex h-16 w-full items-center justify-between px-3 sm:px-4 lg:px-5">
        <Logo className="max-h-10 w-auto" />
        <Link
          href="/admin/login"
          className={cn(buttonVariants({ variant: "ghost", size: "sm", uppercase: true }), "gap-2 px-4")}
        >
          <ShieldCheck className="size-4" strokeWidth={1.75} />
          Ingresar como admin
        </Link>
      </div>
    </header>
  );
}
