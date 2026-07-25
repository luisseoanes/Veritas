"use client";

/**
 * Vista "Simulador": contrafactual de catálogo.
 * Solo pinta `POST /admin/simulate` — no calcula cifras en el front.
 */

import * as React from "react";
import { FlaskConical, Loader2, TriangleAlert, TrendingUp } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { SimulateResponse } from "@/lib/api/types";
import { describeError } from "@/lib/errors";
import { formatCop, formatNumber, formatPercent, humanizeConstraint } from "@/lib/format";

import {
  DashCard,
  DashCounter,
  DashEmpty,
  DashError,
  DashKeyValue,
  DashPanel,
  DashSection,
  FormulaBlock,
  RecommendationBlock,
} from "./dash-ui";

/** Escenario por defecto alineado a la brecha típica de los detectores. */
const DEFAULT_FORM = { power_kw: "22", voltage: "220", price_cop: "8500000" };

export function ViewSimulator() {
  const [form, setForm] = React.useState(DEFAULT_FORM);
  const [data, setData] = React.useState<SimulateResponse | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const field = (key: keyof typeof DEFAULT_FORM) => (event: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [key]: event.target.value }));

  const run = React.useCallback(async () => {
    const power_kw = Number(form.power_kw.replace(",", "."));
    const voltage = Number.parseInt(form.voltage, 10);
    const price_cop = Number.parseInt(form.price_cop.replace(/[^\d]/g, ""), 10);

    if (!(power_kw > 0) || !(voltage > 0) || !(price_cop > 0)) {
      setError("Potencia, voltaje y precio deben ser números mayores que cero.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setData(
        await api.simulate({
          power_kw,
          voltage,
          price_cop,
          kind: "motor",
          features: [],
        }),
      );
    } catch (cause) {
      setData(null);
      setError(describeError(cause));
    } finally {
      setLoading(false);
    }
  }, [form]);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    void run();
  }

  const diagnosis = data?.diagnostico_de_viabilidad ?? null;
  const recovered = data?.clientes_recuperados ?? 0;

  return (
    <>
      <DashSection
        title="Simulador de catálogo"
        subtitle="¿Y si incorporo este producto? Se vuelven a resolver, con el solver real, todas las consultas que quedaron sin solución."
      >
        <form onSubmit={handleSubmit}>
          <DashPanel className="!py-5">
            <div className="grid gap-4 sm:grid-cols-3">
              <div>
                <Label htmlFor="sim-power" className="!text-[12px] !text-dash-text-muted">
                  Potencia (kW)
                </Label>
                <Input
                  id="sim-power"
                  inputMode="decimal"
                  value={form.power_kw}
                  onChange={field("power_kw")}
                  className="mt-1.5"
                  disabled={loading}
                />
              </div>
              <div>
                <Label htmlFor="sim-voltage" className="!text-[12px] !text-dash-text-muted">
                  Voltaje (V)
                </Label>
                <Input
                  id="sim-voltage"
                  inputMode="numeric"
                  value={form.voltage}
                  onChange={field("voltage")}
                  className="mt-1.5"
                  disabled={loading}
                />
              </div>
              <div>
                <Label htmlFor="sim-price" className="!text-[12px] !text-dash-text-muted">
                  Precio estimado (COP)
                </Label>
                <Input
                  id="sim-price"
                  inputMode="numeric"
                  value={form.price_cop}
                  onChange={field("price_cop")}
                  className="mt-1.5"
                  disabled={loading}
                />
              </div>
            </div>

            <div className="mt-5 flex flex-wrap items-center gap-3">
              <Button variant="dashAccent" type="submit" disabled={loading}>
                {loading ? (
                  <Loader2 className="size-3.5 animate-spin" strokeWidth={2} />
                ) : (
                  <FlaskConical className="size-3.5" strokeWidth={1.75} />
                )}
                {loading ? "Simulando…" : "Simular incorporación"}
              </Button>
              <p className="text-[12px] text-dash-text-aux">
                No modifica el catálogo: la simulación se descarta al terminar.
              </p>
            </div>
          </DashPanel>
        </form>
      </DashSection>

      {error ? (
        <div className="mb-6">
          <DashError message={error} onRetry={() => void run()} />
        </div>
      ) : null}

      {data?.status === "SIN_HISTORICO" ? (
        <DashSection title="Resultado">
          <DashEmpty message={data.nota ?? "No hay consultas sin solución registradas."} />
        </DashSection>
      ) : null}

      {data?.status === "OK" ? (
        <>
          <DashSection
            title="Resultado"
            subtitle={`${formatNumber(data.perfiles_distintos)} perfiles distintos · ${formatNumber(data.consultas_perdidas_analizadas)} consultas perdidas re-resueltas.`}
            actions={
              <Badge tone={recovered > 0 ? "ok" : "neutral"}>
                {recovered > 0 ? "Recupera ventas" : "No recupera nada"}
              </Badge>
            }
          >
            <div className="grid gap-3 sm:grid-cols-12">
              <DashCounter
                label="Clientes recuperados"
                value={formatNumber(recovered)}
                tone={recovered > 0 ? "ok" : "neutral"}
                size="hero"
                className="sm:col-span-5"
              />
              <DashCounter
                label="Siguen sin solución"
                value={formatNumber(data.clientes_que_siguen_sin_solucion)}
                tone="neutral"
                size="base"
                className="sm:col-span-3"
              />
              <DashCounter
                label="Tasa de recuperación"
                value={formatPercent(data.tasa_de_recuperacion, 1)}
                tone="accent"
                size="base"
                className="sm:col-span-4"
              />
            </div>

            <DashCard className="mt-4">
              <div className="flex flex-wrap items-end justify-between gap-6">
                <div>
                  <p className="flex items-center gap-1.5 text-[12px] font-medium text-dash-text-muted">
                    <TrendingUp className="size-3.5" strokeWidth={1.75} />
                    Valor recuperable
                  </p>
                  <p className="tnum mt-2 text-[clamp(1.75rem,3vw,2.35rem)] font-semibold leading-none tracking-tight text-dash-text">
                    {formatCop(data.valor_recuperable_cop)}
                  </p>
                </div>
                {data.productos_simulados?.[0] ? (
                  <p className="font-mono text-[11px] text-dash-text-aux">
                    {data.productos_simulados[0].id}
                  </p>
                ) : null}
              </div>
              {data.formula ? <div className="mt-4"><FormulaBlock formula={data.formula} /></div> : null}
            </DashCard>
          </DashSection>

          {diagnosis?.length ? (
            <DashSection
              title="Diagnóstico de viabilidad"
              subtitle="El producto no forma ninguna configuración vendible. Añadirlo, por sí solo, no habilita ventas."
            >
              <div className="grid gap-4">
                {diagnosis.map((item) => (
                  <DashCard key={item.producto} className="flex flex-col gap-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="flex size-8 items-center justify-center rounded-lg bg-[var(--dash-warn-soft)] text-dash-warn">
                        <TriangleAlert className="size-4" strokeWidth={1.75} />
                      </span>
                      <Badge tone="warn">{item.motivo}</Badge>
                      <code className="font-mono text-[11px] text-dash-text-aux">{item.producto}</code>
                    </div>
                    <p className="text-[13px] leading-relaxed text-dash-text">{item.explicacion}</p>
                    {item.para_cerrar_la_brecha ? (
                      <RecommendationBlock text={item.para_cerrar_la_brecha} />
                    ) : null}
                  </DashCard>
                ))}
              </div>
            </DashSection>
          ) : null}

          {data.detalle_recuperados?.length ? (
            <DashSection
              title="Perfiles recuperados"
              subtitle="Consultas que pasan de imposibles a vendibles con el producto nuevo."
            >
              <div className="grid gap-4 lg:grid-cols-2">
                {data.detalle_recuperados.map((profile, index) => (
                  <DashCard key={index} className="grid grid-cols-2 gap-4">
                    <DashKeyValue
                      label="Perfil"
                      value={profileLabel(profile.perfil.power_kw, profile.perfil.voltage)}
                    />
                    <DashKeyValue label="Clientes" value={formatNumber(profile.clientes)} />
                    <DashKeyValue
                      label="Presupuesto promedio"
                      value={formatCop(profile.presupuesto_promedio_cop)}
                    />
                    <DashKeyValue
                      label="Valor recuperable"
                      value={formatCop(profile.valor_recuperable_cop)}
                      tone="ok"
                    />
                  </DashCard>
                ))}
              </div>
            </DashSection>
          ) : null}

          {data.detalle_no_recuperados?.length ? (
            <DashSection
              title="Siguen bloqueados"
              subtitle="Clientes que este producto no rescata, y la restricción que se lo impide."
            >
              <div className="grid gap-4 lg:grid-cols-2">
                {data.detalle_no_recuperados.map((profile, index) => (
                  <DashCard key={index} className="flex flex-col gap-3">
                    <div className="grid grid-cols-2 gap-4">
                      <DashKeyValue
                        label="Perfil"
                        value={profileLabel(profile.perfil.power_kw, profile.perfil.voltage)}
                      />
                      <DashKeyValue label="Clientes" value={formatNumber(profile.clientes)} />
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {(profile.sigue_bloqueado_por ?? []).map((constraint) => (
                        <Badge key={constraint} size="sm" className="font-mono">
                          {humanizeConstraint(constraint)}
                        </Badge>
                      ))}
                    </div>
                  </DashCard>
                ))}
              </div>
            </DashSection>
          ) : null}

          {data.metodo ? (
            <DashSection title="Método">
              <DashCard>
                <p className="text-[13px] leading-relaxed text-dash-text-muted">{data.metodo}</p>
              </DashCard>
            </DashSection>
          ) : null}
        </>
      ) : null}
    </>
  );
}

function profileLabel(power: number | null | undefined, voltage: number | null | undefined): string {
  const parts: string[] = [];
  if (power !== null && power !== undefined) parts.push(`${formatNumber(power, 1)} kW`);
  if (voltage !== null && voltage !== undefined) parts.push(`${formatNumber(voltage)} V`);
  return parts.length ? parts.join(" · ") : "—";
}
