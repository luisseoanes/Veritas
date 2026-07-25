"use client";

import * as React from "react";
import { usePathname, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { ToastProvider } from "@/components/ui/toast";
import { getAdminToken } from "@/lib/admin-token";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // El login vive bajo /admin pero no puede exigir token.
  if (pathname?.startsWith("/admin/login")) return <>{children}</>;

  return (
    <ToastProvider>
      <AdminGuard>{children}</AdminGuard>
    </ToastProvider>
  );
}

/** Sin token en cliente no se pinta el panel; un 401 posterior lo expulsa (§5). */
function AdminGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [allowed, setAllowed] = React.useState<boolean | null>(null);

  React.useEffect(() => {
    if (getAdminToken()) {
      setAllowed(true);
      return;
    }
    setAllowed(false);
    router.replace("/admin/login");
  }, [router]);

  if (allowed !== true) {
    return (
      <div className="flex h-dvh items-center justify-center bg-dash-bg text-dash-text-muted">
        <Loader2 className="size-5 animate-spin" strokeWidth={2} />
      </div>
    );
  }

  return <>{children}</>;
}
