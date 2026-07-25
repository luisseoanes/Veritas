"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2 } from "lucide-react";

import { ViewChatbot } from "@/components/admin/view-chatbot";
import { ViewFrontier } from "@/components/admin/view-frontier";
import { ViewObjective } from "@/components/admin/view-objective";
import { ViewOpportunities } from "@/components/admin/view-opportunities";
import { ViewSimulator } from "@/components/admin/view-simulator";
import { ViewSummary } from "@/components/admin/view-summary";
import { parseView, type AdminView } from "@/components/admin/views";
import { AdminContent, AdminShell } from "@/components/layout/admin-shell";
import { useToast } from "@/components/ui/toast";
import { useDashboardPolling } from "@/hooks/use-dashboard-polling";
import { api } from "@/lib/api";
import { clearAdminToken } from "@/lib/admin-token";
import { objectiveLabel } from "@/lib/demo";
import { describeError } from "@/lib/errors";

export default function AdminPage() {
  return (
    <React.Suspense fallback={<ShellFallback />}>
      <AdminDashboard />
    </React.Suspense>
  );
}

function ShellFallback() {
  return (
    <div className="flex h-dvh items-center justify-center bg-dash-bg text-dash-text-muted">
      <Loader2 className="size-5 animate-spin" strokeWidth={2} />
    </div>
  );
}

function AdminDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();

  const view = parseView(searchParams.get("view"));
  const { data, error, loading, refresh } = useDashboardPolling(2000);

  const [optimisticObjective, setOptimisticObjective] = React.useState<string | null>(null);
  const [resetting, setResetting] = React.useState(false);

  const serverObjective = data?.resumen.objetivo_activo;
  React.useEffect(() => {
    if (optimisticObjective && serverObjective === optimisticObjective) {
      setOptimisticObjective(null);
    }
  }, [optimisticObjective, serverObjective]);

  const activeObjective = optimisticObjective ?? serverObjective;

  function changeView(next: AdminView) {
    router.replace(next === "resumen" ? "/admin" : `/admin?view=${next}`, { scroll: false });
  }

  async function handleReset() {
    if (resetting) return;
    setResetting(true);
    try {
      const { data: response, simulado } = await api.demoReset({ keep_history: true });
      refresh();
      toast(
        simulado
          ? {
              title: "Reset simulado",
              description:
                "El backend todavía no expone POST /demo/reset. El estado real del servidor no cambió.",
              tone: "warn",
            }
          : {
              title: "Demo reiniciada",
              description: response.historico_conservado
                ? "Se conservó el histórico de conversaciones."
                : "El histórico fue borrado por el backend.",
              tone: "ok",
            },
      );
    } catch (cause) {
      toast({ title: "No se pudo reiniciar", description: describeError(cause), tone: "danger" });
    } finally {
      setResetting(false);
    }
  }

  function handleLogout() {
    clearAdminToken();
    router.replace("/admin/login");
  }

  return (
    <AdminShell
      view={view}
      onViewChange={changeView}
      objetivoActivo={activeObjective}
      onReset={handleReset}
      resetting={resetting}
      onLogout={handleLogout}
      fill={view === "chatbot"}
    >
      {view === "chatbot" ? (
        <ViewChatbot />
      ) : (
        <AdminContent>
          {view === "resumen" ? (
            <ViewSummary data={data} loading={loading} error={error} onRetry={refresh} />
          ) : null}

          {view === "objetivo" ? (
            <ViewObjective
              activo={activeObjective}
              onChanged={(response) => {
                setOptimisticObjective(response.activo);
                refresh();
                toast({
                  title: `Objetivo: ${objectiveLabel(response.activo)}`,
                  description:
                    "El agente lo respeta desde la siguiente consulta del cliente y la frontera reubica el punto elegido.",
                  tone: "ok",
                });
              }}
              onError={(message) =>
                toast({ title: "No se pudo cambiar el objetivo", description: message, tone: "danger" })
              }
            />
          ) : null}

          {view === "frontera" ? <ViewFrontier activo={activeObjective} /> : null}

          {view === "oportunidades" ? (
            <ViewOpportunities data={data} loading={loading} error={error} onRetry={refresh} />
          ) : null}

          {view === "simulador" ? <ViewSimulator /> : null}
        </AdminContent>
      )}
    </AdminShell>
  );
}
