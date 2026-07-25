"use client";

/**
 * Vista "Simulador": el contrafactual de catálogo.
 *
 * Responde "¿y si incorporo este producto, cuántas ventas perdidas recupero?".
 * La cifra NO se estima aquí ni en el backend: sale de volver a resolver, con el
 * solver real, las consultas que de verdad quedaron sin solución.
 *
 * Por eso esta vista no calcula nada — solo pinta lo que devuelve
 * `POST /admin/simulate`. Si algún día muestra un número que el backend no
 * mandó, está mal escrita.
 */

import { useState } from "react";
import { FlaskConical, TriangleAlert, TrendingUp } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";
import type { SimulateResponse } from "@/lib/api/types";
import { formatCop, formatNumber, formatPercent, humanizeConstraint } from "@/lib/format";

import {
  DashCard,
  DashEmpty,
  DashError,
  DashKeyValue,
  DashSection,
  FormulaBlock,
  RecommendationBlock,
} from "./dash-ui";

/** Escenario por defecto: la brecha que los detectores ya señalan (22 kW / 220 V). */
const DEFAULT_FORM = { power_kw: "22", voltage: "220", price_cop: "8500000" };

export function ViewSimulator() {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [data, setData] = useState<SimulateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const field = (key: keyof typeof form) => (event: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [key]: event.target.value }));

  async function run() {
    const power_kw = Number(form.power_kw);
    const voltage = Number(form.voltage);
    const price_cop = Number(form.price_cop);

    if (!(power_kw > 0) || !(voltage > 0) || !(price_cop > 0)) {
      setError("Potencia, voltaje y precio deben ser números mayores que cero.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      setData(await api.simulate({ power_kw, voltage, price_cop, kind: "motor" }));
    } catch (err) {
      setData(null);
      setError(
        err instanceof ApiError ? err.message : "No se pudo ejecutar la simulación.",
      );
    } finally {
      setLoading(false);
    }
  }

  const diagnosis = data?.diagnostico_de_viabilidad ?? null;
  const recovered = data?.clientes_recuperados ?? 0;

  return (
    <>
      <DashSection
        title="Simulador de catálogo"
        subtitle="¿Y si incorporo este producto? Se vuelven a resolver, con el solver real, todas las consultas que quedaron sin solución."
      >
        <DashCard className="p-6">
          <div className="grid gap-4 sm:grid-cols-3">
            <label className="block">
              <span className="mb-2 block text-xs uppercase tracking-wide text-dash-muted">
                Potencia (kW)
              </span>
              <Input inputMode="decimal" value={form.power_kw} onChange={field("power_kw")} />
            </label>
            <label className="block">
              <span className="mb-2 block text-xs uppercase tracking-wide text-dash-muted">
                Voltaje (V)
              </span>
              <Input inputMode="numeric" value={form.voltage} onChange={field("voltage")} />
            </label>
            <label className="block">
              <span className="mb-2 block text-xs uppercase tracking-wide text-dash-muted">
                Precio estimado (COP)
              </span>
              <Input inputMode="numeric" value={form.price_cop} onChange={field("price_cop")} />
            </label>
          </div>

          <div className="mt-5 flex items-center gap-3">
            <Button onClick={run} disabled={loading}>
              <FlaskConical className="mr-2 h-4 w-4" />
              {loading ? "Simulando…" : "Simular incorporación"}
            </Button>
            <span className="text-xs text-dash-muted">
              No modifica el catálogo: la simulación se descarta al terminar.
            </span>
          </div>
        </DashCard>
      </DashSection>

      {error && (
        <DashSection title="Error">
          <DashError message={error} onRetry={run} />
        </DashSection>
      )}

      {data?.status === "SIN_HISTORICO" && (
        <DashSection title="Resultado">
          <DashEmpty message={data.nota ?? "No hay consultas sin solución registradas."} />
        </DashSection>
      )}

      {data?.status === "OK" && (
        <>
          <DashSection
            title="Resultado"
            subtitle={`${formatNumber(data.perfiles_distintos)} perfiles distintos re-resueltos sobre ${formatNumber(data.consultas_perdidas_analizadas)} consultas perdidas.`}
            actions={
              <Badge tone={recovered > 0 ? "ok" : "neutral"}>
                {recovered > 0 ? "Recupera ventas" : "No recupera nada"}
              </Badge>
            }
          >
            <div className="grid gap-6 lg:grid-cols-3">
              <DashCard className="p-6">
                <DashKeyValue label="Clientes recuperados" value={formatNumber(recovered)} />
                <DashKeyValue
                  label="Siguen sin solución"
                  value={formatNumber(data.clientes_que_siguen_sin_solucion)}
                />
                <DashKeyValue
                  label="Tasa de recuperación"
                  value={formatPercent(data.tasa_de_recuperacion, 1)}
                />
              </DashCard>

              <DashCard className="p-6 lg:col-span-2">
                <div className="mb-3 flex items-center gap-2 text-dash-text">
                  <TrendingUp className="h-4 w-4" />
                  <span className="text-sm font-medium">Valor recuperable</span>
                </div>
                <p className="text-3xl font-medium text-dash-text">
                  {formatCop(data.valor_recuperable_cop)}
                </p>
                {data.formula && <FormulaBlock formula={data.formula} />}
              </DashCard>
            </div>
          </DashSection>

          {/* El caso más valioso: cero recuperados CON explicación. */}
          {diagnosis?.length ? (
            <DashSection
              title="Diagnóstico de viabilidad"
              subtitle="El producto no forma ninguna configuración vendible. Añadirlo, por sí solo, no habilita ventas."
            >
              <div className="grid gap-6">
                {diagnosis.map((d) => (
                  <DashCard key={d.producto} className="p-6">
                    <div className="mb-3 flex items-center gap-2">
                      <TriangleAlert className="h-4 w-4 text-dash-warn" />
                      <Badge tone="warn">{d.motivo}</Badge>
                    </div>
                    <p className="text-sm leading-relaxed text-dash-text">{d.explicacion}</p>
                    {d.para_cerrar_la_brecha && (
                      <RecommendationBlock text={d.para_cerrar_la_brecha} />
                    )}
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
              <div className="grid gap-6 lg:grid-cols-2">
                {data.detalle_recuperados.map((p, i) => (
                  <DashCard key={i} className="p-6">
                    <DashKeyValue
                      label="Perfil"
                      value={`${formatNumber(p.perfil.power_kw, 1)} kW · ${formatNumber(p.perfil.voltage)} V`}
                    />
                    <DashKeyValue label="Clientes" value={formatNumber(p.clientes)} />
                    <DashKeyValue
                      label="Presupuesto promedio"
                      value={formatCop(p.presupuesto_promedio_cop)}
                    />
                    <DashKeyValue
                      label="Valor recuperable"
                      value={formatCop(p.valor_recuperable_cop)}
                    />
                  </DashCard>
                ))}
              </div>
            </DashSection>
          ) : null}

          {data.detalle_no_recuperados?.length ? (
            <DashSection
              title="Siguen bloqueados"
              subtitle="Clientes que este producto NO rescata, y la restricción que se lo impide. Es el límite honesto de la inversión."
            >
              <div className="grid gap-6 lg:grid-cols-2">
                {data.detalle_no_recuperados.map((p, i) => (
                  <DashCard key={i} className="p-6">
                    <DashKeyValue
                      label="Perfil"
                      value={`${formatNumber(p.perfil.power_kw, 1)} kW · ${formatNumber(p.perfil.voltage)} V`}
                    />
                    <DashKeyValue label="Clientes" value={formatNumber(p.clientes)} />
                    <div className="mt-3 flex flex-wrap gap-2">
                      {(p.sigue_bloqueado_por ?? []).map((c) => (
                        <Badge key={c} tone="neutral">
                          {humanizeConstraint(c)}
                        </Badge>
                      ))}
                    </div>
                  </DashCard>
                ))}
              </div>
            </DashSection>
          ) : null}

          {data.metodo && (
            <DashSection title="Método">
              <DashCard className="p-6">
                <p className="text-sm leading-relaxed text-dash-muted">{data.metodo}</p>
              </DashCard>
            </DashSection>
          )}
        </>
      )}
    </>
  );
}
