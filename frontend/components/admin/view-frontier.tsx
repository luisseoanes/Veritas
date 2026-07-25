"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { CircleOff, Loader2, Sparkles, Target } from "lucide-react";
import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { FrontierPoint, FrontierResponse, SolveRequest } from "@/lib/api/types";
import { isFrontierOk } from "@/lib/api/types";
import { DEMO_FRONTIER_BODY } from "@/lib/demo";
import { describeError } from "@/lib/errors";
import { formatCop, formatCopCompact, formatNumber, humanizeConstraint } from "@/lib/format";
import { cn } from "@/lib/utils";

import { CHART } from "./chart-tokens";
import { DashCard, DashError, DashSection } from "./dash-ui";

interface PointDatum {
  x: number;
  y: number;
  ids: string[];
  availability: number;
  efficiency: number;
  precio: number;
}

interface ScenarioForm {
  power_kw: string;
  voltage: string;
  budget_cop: string;
  features: string;
  require_stock: boolean;
}

const INITIAL_FORM: ScenarioForm = {
  power_kw: String(DEMO_FRONTIER_BODY.power_kw ?? ""),
  voltage: String(DEMO_FRONTIER_BODY.voltage ?? ""),
  budget_cop: String(DEMO_FRONTIER_BODY.budget_cop ?? ""),
  features: (DEMO_FRONTIER_BODY.features ?? []).join(", "),
  require_stock: DEMO_FRONTIER_BODY.require_stock ?? true,
};

export function ViewFrontier({ activo }: { activo: string | undefined }) {
  const [form, setForm] = React.useState<ScenarioForm>(INITIAL_FORM);
  const [result, setResult] = React.useState<FrontierResponse | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const compute = React.useCallback(async (scenario: SolveRequest) => {
    setLoading(true);
    setError(null);
    try {
      setResult(await api.frontier(scenario));
    } catch (cause) {
      setError(describeError(cause));
    } finally {
      setLoading(false);
    }
  }, []);

  // Se calcula el escenario del guion al entrar: la vista nunca aparece vacía.
  const bootstrapped = React.useRef(false);
  React.useEffect(() => {
    if (bootstrapped.current) return;
    bootstrapped.current = true;
    void compute(DEMO_FRONTIER_BODY);
  }, [compute]);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const scenario = toSolveRequest(form);
    if (!scenario) {
      setError("Envía al menos un requerimiento con valor mayor que cero.");
      return;
    }
    void compute(scenario);
  }

  function useDemoScenario() {
    setForm(INITIAL_FORM);
    void compute(DEMO_FRONTIER_BODY);
  }

  return (
    <DashSection
      title="Frontera de Pareto"
      subtitle="El front manda el escenario técnico; el backend resuelve, devuelve la frontera y qué punto elegiría cada objetivo. El objetivo activo vive en el servidor, no en este formulario."
    >
      <form onSubmit={handleSubmit}>
        <DashCard>
          <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
            <Field
              label="Potencia (kW)"
              value={form.power_kw}
              onChange={(value) => setForm((current) => ({ ...current, power_kw: value }))}
              placeholder="5.5"
              inputMode="decimal"
            />
            <Field
              label="Tensión (V)"
              value={form.voltage}
              onChange={(value) => setForm((current) => ({ ...current, voltage: value }))}
              placeholder="220"
              inputMode="numeric"
            />
            <Field
              label="Presupuesto (COP)"
              value={form.budget_cop}
              onChange={(value) => setForm((current) => ({ ...current, budget_cop: value }))}
              placeholder="8000000"
              inputMode="numeric"
            />
            <Field
              label="Características"
              value={form.features}
              onChange={(value) => setForm((current) => ({ ...current, features: value }))}
              placeholder="soft_start, modbus"
            />
          </div>

          <div className="mt-6 flex flex-wrap items-center gap-6">
            <label className="flex cursor-pointer items-center gap-2.5 text-[14px] text-dash-text-muted">
              <input
                type="checkbox"
                checked={form.require_stock}
                onChange={(event) =>
                  setForm((current) => ({ ...current, require_stock: event.target.checked }))
                }
                className="size-4 accent-[var(--dash-accent)]"
              />
              Exigir stock disponible
            </label>

            <div className="ml-auto flex flex-wrap items-center gap-3">
              <Button variant="dash" size="md" onClick={useDemoScenario} disabled={loading}>
                <Sparkles className="size-4" strokeWidth={1.75} />
                Escenario demo
              </Button>
              <Button variant="dashAccent" size="md" type="submit" disabled={loading}>
                {loading ? (
                  <Loader2 className="size-4 animate-spin" strokeWidth={2} />
                ) : (
                  <Target className="size-4" strokeWidth={2} />
                )}
                Calcular frontera
              </Button>
            </div>
          </div>
        </DashCard>
      </form>

      {error ? (
        <div className="mt-6">
          <DashError message={error} onRetry={() => void compute(toSolveRequest(form) ?? DEMO_FRONTIER_BODY)} />
        </div>
      ) : null}

      {result ? (
        isFrontierOk(result) ? (
          <FrontierChart result={result} activo={activo} />
        ) : (
          <UnsatPanel core={result.nucleo_insatisfacible} />
        )
      ) : null}
    </DashSection>
  );
}

function FrontierChart({
  result,
  activo,
}: {
  result: Extract<FrontierResponse, { status: "OK" }>;
  activo: string | undefined;
}) {
  const frontier = React.useMemo(() => result.frontera.map(toDatum), [result.frontera]);
  const dominated = React.useMemo(() => result.dominadas.map(toDatum), [result.dominadas]);

  const activeKey = activo ?? "balanced";
  const chosen = result.elegida_por_objetivo[activeKey];
  const chosenDatum = React.useMemo(() => {
    if (!chosen) return [];
    const match = frontier.find((point) => sameIds(point.ids, chosen.ids));
    return match ? [match] : [];
  }, [chosen, frontier]);

  return (
    <>
      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <LegendCard
          title="Frontera"
          swatch={CHART.frontier}
          value={`${formatNumber(result.frontera.length)} puntos`}
          description="Configuraciones no dominadas: mejorar una dimensión obliga a ceder en otra."
        />
        <LegendCard
          title="Dominadas"
          swatch={CHART.dominated}
          value={`${formatNumber(result.dominadas.length)} puntos`}
          description="Peores en todo. Ningún objetivo puede elegirlas: son inalcanzables por construcción."
        />
        <LegendCard
          title="Elegida"
          swatch={CHART.chosenFill}
          value={chosen ? formatCop(chosen.precio_cop) : "—"}
          description="El punto que selecciona el objetivo activo del servidor."
          highlight
        />
      </div>

      <DashCard className="mt-6">
        <div className="h-[420px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 12, right: 24, bottom: 44, left: 28 }}>
              <CartesianGrid stroke={CHART.grid} />
              <XAxis
                type="number"
                dataKey="x"
                name="Costo"
                domain={["dataMin - 300000", "dataMax + 300000"]}
                tickFormatter={(value: number) => formatCopCompact(value)}
                stroke={CHART.axis}
                tick={{ fill: CHART.axis, fontSize: 12 }}
                label={{
                  value: "Costo total (COP)",
                  position: "insideBottom",
                  offset: -24,
                  fill: CHART.axis,
                  fontSize: 12,
                }}
              />
              <YAxis
                type="number"
                dataKey="y"
                name="Margen"
                domain={["dataMin - 150000", "dataMax + 150000"]}
                tickFormatter={(value: number) => formatCopCompact(value)}
                stroke={CHART.axis}
                tick={{ fill: CHART.axis, fontSize: 12 }}
                width={80}
                label={{
                  value: "Margen (COP)",
                  angle: -90,
                  position: "insideLeft",
                  fill: CHART.axis,
                  fontSize: 12,
                }}
              />
              <Tooltip content={<FrontierTooltip />} />
              <Scatter name="Dominadas" data={dominated} fill={CHART.dominated} opacity={0.65} />
              <Scatter name="Frontera" data={frontier} fill={CHART.frontier} />
              <Scatter name="Elegida" data={chosenDatum} shape={<ChosenDot />} />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </DashCard>

      {chosen ? (
        <DashCard className="mt-6 border-dash-accent">
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div className="min-w-0">
              <p className="text-[13px] font-medium uppercase tracking-[0.12em] text-dash-accent">
                Configuración elegida por el objetivo activo
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {chosen.ids.map((id) => (
                  <code
                    key={id}
                    className="rounded-full border border-dash-border bg-dash-surface-2 px-3 py-1 font-mono text-[12px] text-dash-text"
                  >
                    {id}
                  </code>
                ))}
              </div>
            </div>

            <motion.p
              key={chosen.precio_cop}
              initial={{ opacity: 0, y: 10, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ type: "spring", stiffness: 240, damping: 22 }}
              className="tnum text-[clamp(2rem,3.4vw,2.75rem)] font-medium leading-none text-dash-accent"
            >
              {formatCop(chosen.precio_cop)}
            </motion.p>
          </div>
        </DashCard>
      ) : null}
    </>
  );
}

function UnsatPanel({ core }: { core: string[] }) {
  return (
    <DashCard className="mt-6 border-[color-mix(in_oklab,var(--dash-danger),transparent_60%)]">
      <div className="flex items-start gap-4">
        <span className="flex size-11 shrink-0 items-center justify-center rounded-full bg-[var(--dash-danger-soft)] text-dash-danger">
          <CircleOff className="size-5" strokeWidth={1.75} />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="text-[19px] font-medium text-dash-text">Este escenario no tiene frontera</h3>
          <p className="mt-2 max-w-2xl text-[14px] leading-relaxed text-dash-text-muted">
            No existe configuración válida: el solver devolvió el núcleo mínimo insatisfacible, es
            decir el conjunto de restricciones que hace imposible el problema. Ajusta el escenario y
            vuelve a calcular.
          </p>
          <div className="mt-5 flex flex-wrap gap-2">
            {core.map((constraint) => (
              <Badge key={constraint} tone="danger" size="lg" className="font-mono">
                {humanizeConstraint(constraint)}
              </Badge>
            ))}
          </div>
        </div>
      </div>
    </DashCard>
  );
}

function LegendCard({
  title,
  swatch,
  value,
  description,
  highlight = false,
}: {
  title: string;
  swatch: string;
  value: string;
  description: string;
  highlight?: boolean;
}) {
  return (
    <DashCard className={cn(highlight && "border-dash-accent")}>
      <div className="flex items-center gap-3">
        <span className="size-3 shrink-0 rounded-full" style={{ backgroundColor: swatch }} />
        <p className="text-[13px] font-medium uppercase tracking-[0.12em] text-dash-text-muted">
          {title}
        </p>
      </div>
      <p className="tnum mt-4 text-[26px] font-medium leading-none text-dash-text">{value}</p>
      <p className="mt-3 text-[13px] leading-relaxed text-dash-text-muted">{description}</p>
    </DashCard>
  );
}

function ChosenDot({ cx, cy }: { cx?: number; cy?: number }) {
  if (cx === undefined || cy === undefined) return null;
  return (
    <g>
      <circle cx={cx} cy={cy} r={18} fill={CHART.chosenFill} className="chosen-halo" />
      <circle cx={cx} cy={cy} r={8} fill={CHART.chosenFill} stroke={CHART.chosen} strokeWidth={2} />
    </g>
  );
}

function FrontierTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload?: PointDatum }>;
}) {
  const datum = payload?.[0]?.payload;
  if (!active || !datum) return null;

  return (
    <div
      className="rounded-[var(--radius-card)] border p-4 shadow-[var(--elev-3)]"
      style={{ backgroundColor: CHART.surface, borderColor: CHART.border }}
    >
      <p className="font-mono text-[12px] leading-relaxed text-dash-text">{datum.ids.join(" · ")}</p>
      <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-2 text-[12px]">
        <TooltipRow label="Precio" value={formatCop(datum.precio)} />
        <TooltipRow label="Costo" value={formatCop(datum.x)} />
        <TooltipRow label="Margen" value={formatCop(datum.y)} />
        <TooltipRow label="Disponibilidad" value={formatNumber(datum.availability)} />
        <TooltipRow label="Eficiencia" value={`${formatNumber(datum.efficiency, 1)} %`} />
      </dl>
    </div>
  );
}

function TooltipRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-dash-text-aux">{label}</dt>
      <dd className="tnum font-medium text-dash-text">{value}</dd>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  inputMode,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  inputMode?: "numeric" | "decimal";
}) {
  const id = `frontier-${label.toLowerCase().replace(/[^a-z]+/g, "-")}`;
  return (
    <div>
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        value={value}
        placeholder={placeholder}
        inputMode={inputMode}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2"
      />
    </div>
  );
}

function toDatum(point: FrontierPoint): PointDatum {
  return {
    x: point.objectives.cost,
    y: point.objectives.margin,
    ids: point.ids,
    availability: point.objectives.availability,
    efficiency: point.objectives.efficiency,
    precio: point.total_price_cop,
  };
}

function sameIds(a: string[], b: string[]): boolean {
  return a.length === b.length && a.every((id, index) => id === b[index]);
}

/** Solo viajan los campos con valor válido: el backend exige `gt=0` si se envían. */
function toSolveRequest(form: ScenarioForm): SolveRequest | null {
  const scenario: SolveRequest = { require_stock: form.require_stock };

  const power = Number.parseFloat(form.power_kw.replace(",", "."));
  if (Number.isFinite(power) && power > 0) scenario.power_kw = power;

  const voltage = Number.parseInt(form.voltage, 10);
  if (Number.isFinite(voltage) && voltage > 0) scenario.voltage = voltage;

  const budget = Number.parseInt(form.budget_cop.replace(/[^\d]/g, ""), 10);
  if (Number.isFinite(budget) && budget > 0) scenario.budget_cop = budget;

  const features = form.features
    .split(",")
    .map((feature) => feature.trim())
    .filter(Boolean);
  if (features.length) scenario.features = features;

  const hasRequirement =
    scenario.power_kw !== undefined ||
    scenario.voltage !== undefined ||
    scenario.budget_cop !== undefined ||
    (scenario.features?.length ?? 0) > 0 ||
    form.require_stock;

  return hasRequirement ? scenario : null;
}
