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
  ZAxis,
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

import { CHART } from "./chart-tokens";
import { DashCard, DashCounter, DashError, DashPanel, DashSection } from "./dash-ui";

interface PointDatum {
  x: number;
  y: number;
  z: number;
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
      subtitle="Escenario técnico → solver → frontera. El objetivo activo elige un punto válido; nunca sale de la frontera."
    >
      <form onSubmit={handleSubmit}>
        <DashPanel className="!py-5">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
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

          <div className="mt-5 flex flex-wrap items-center gap-4">
            <label className="flex cursor-pointer items-center gap-2 text-[13px] text-dash-text-muted">
              <input
                type="checkbox"
                checked={form.require_stock}
                onChange={(event) =>
                  setForm((current) => ({ ...current, require_stock: event.target.checked }))
                }
                className="size-3.5 accent-[var(--dash-accent)]"
              />
              Exigir stock disponible
            </label>

            <div className="ml-auto flex flex-wrap items-center gap-2">
              <Button variant="dash" size="md" onClick={useDemoScenario} disabled={loading}>
                <Sparkles className="size-3.5" strokeWidth={1.75} />
                Escenario demo
              </Button>
              <Button variant="dashAccent" size="md" type="submit" disabled={loading}>
                {loading ? (
                  <Loader2 className="size-3.5 animate-spin" strokeWidth={2} />
                ) : (
                  <Target className="size-3.5" strokeWidth={2} />
                )}
                Calcular frontera
              </Button>
            </div>
          </div>
        </DashPanel>
      </form>

      {error ? (
        <div className="mt-4">
          <DashError
            message={error}
            onRetry={() => void compute(toSolveRequest(form) ?? DEMO_FRONTIER_BODY)}
          />
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
    return match ? [{ ...match, z: 220 }] : [];
  }, [chosen, frontier]);

  return (
    <div className="mt-6 space-y-4">
      <div className="grid gap-3 sm:grid-cols-12">
        <DashCounter
          label="Puntos en frontera"
          value={formatNumber(result.frontera.length)}
          tone="accent"
          size="hero"
          className="sm:col-span-5"
        />
        <DashCounter
          label="Dominadas"
          value={formatNumber(result.dominadas.length)}
          tone="neutral"
          size="base"
          className="sm:col-span-3"
        />
        <DashCounter
          label="Elegida"
          value={chosen ? formatCopCompact(chosen.precio_cop) : "—"}
          tone="warn"
          size="base"
          className="sm:col-span-4"
        />
      </div>

      <DashPanel className="overflow-hidden !px-4 !py-5 sm:!px-6">
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3 px-1">
          <div>
            <p className="text-[13px] font-semibold text-dash-text">Costo × margen</p>
            <p className="mt-0.5 text-[12px] text-dash-text-muted">
              Cada punto es una configuración válida. El ámbar es la elegida por el objetivo activo.
            </p>
          </div>
          <div className="flex flex-wrap gap-4">
            <Swatch color={CHART.frontier} label="Frontera" />
            <Swatch color={CHART.dominated} label="Dominadas" />
            <Swatch color={CHART.chosenFill} label="Elegida" />
          </div>
        </div>

        <div className="relative h-[420px] w-full overflow-hidden rounded-[var(--radius-card)] border border-dash-border bg-dash-surface-2">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 24, right: 24, bottom: 44, left: 16 }}>
              <CartesianGrid stroke={CHART.grid} strokeDasharray="3 6" vertical={false} />
              <XAxis
                type="number"
                dataKey="x"
                name="Costo"
                domain={["dataMin - 300000", "dataMax + 300000"]}
                tickFormatter={(value: number) => formatCopCompact(value)}
                stroke={CHART.axis}
                tick={{ fill: CHART.axis, fontSize: 11 }}
                axisLine={{ stroke: CHART.border }}
                tickLine={false}
                label={{
                  value: "Costo total (COP)",
                  position: "insideBottom",
                  offset: -26,
                  fill: CHART.axis,
                  fontSize: 11,
                }}
              />
              <YAxis
                type="number"
                dataKey="y"
                name="Margen"
                domain={["dataMin - 150000", "dataMax + 150000"]}
                tickFormatter={(value: number) => formatCopCompact(value)}
                stroke={CHART.axis}
                tick={{ fill: CHART.axis, fontSize: 11 }}
                axisLine={{ stroke: CHART.border }}
                tickLine={false}
                width={72}
                label={{
                  value: "Margen (COP)",
                  angle: -90,
                  position: "insideLeft",
                  fill: CHART.axis,
                  fontSize: 11,
                }}
              />
              <ZAxis type="number" dataKey="z" range={[36, 180]} />
              <Tooltip
                content={<FrontierTooltip />}
                cursor={{ strokeDasharray: "3 4", stroke: CHART.axis }}
              />
              <Scatter
                name="Dominadas"
                data={dominated}
                fill={CHART.dominated}
                fillOpacity={0.7}
                shape={<SoftDot fill={CHART.dominated} r={4.5} />}
              />
              <Scatter
                name="Frontera"
                data={frontier}
                fill={CHART.frontier}
                shape={<SoftDot fill={CHART.frontier} r={5.5} />}
              />
              <Scatter name="Elegida" data={chosenDatum} shape={<ChosenDot />} />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </DashPanel>

      {chosen ? (
        <DashCard>
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div className="min-w-0">
              <p className="text-[12px] font-medium text-dash-warn">Configuración elegida</p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {chosen.ids.map((id) => (
                  <code
                    key={id}
                    className="rounded-[var(--radius-control)] border border-dash-border bg-dash-surface-2 px-2.5 py-1 font-mono text-[11px] text-dash-text-muted"
                  >
                    {id}
                  </code>
                ))}
              </div>
            </div>

            <motion.p
              key={chosen.precio_cop}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
              className="tnum text-[clamp(1.75rem,3vw,2.35rem)] font-semibold leading-none tracking-tight text-dash-text"
            >
              {formatCop(chosen.precio_cop)}
            </motion.p>
          </div>
        </DashCard>
      ) : null}
    </div>
  );
}

function SoftDot({
  cx,
  cy,
  fill,
  r = 5,
}: {
  cx?: number;
  cy?: number;
  fill: string;
  r?: number;
}) {
  if (cx === undefined || cy === undefined) return null;
  return <circle cx={cx} cy={cy} r={r} fill={fill} />;
}

function ChosenDot({ cx, cy }: { cx?: number; cy?: number }) {
  if (cx === undefined || cy === undefined) return null;
  return (
    <g>
      <circle cx={cx} cy={cy} r={14} fill={CHART.chosenHalo} className="chosen-halo" />
      <circle
        cx={cx}
        cy={cy}
        r={6}
        fill={CHART.chosenFill}
        stroke="#ffffff"
        strokeWidth={2}
      />
    </g>
  );
}

function Swatch({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-[12px] text-dash-text-muted">
      <span className="size-2 rounded-full" style={{ backgroundColor: color }} />
      {label}
    </span>
  );
}

function UnsatPanel({ core }: { core: string[] }) {
  return (
    <DashCard className="mt-6">
      <div className="flex items-start gap-3.5">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-[var(--dash-danger-soft)] text-dash-danger">
          <CircleOff className="size-4" strokeWidth={1.75} />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="text-[15px] font-semibold text-dash-text">Este escenario no tiene frontera</h3>
          <p className="mt-1.5 max-w-2xl text-[13px] leading-relaxed text-dash-text-muted">
            No existe configuración válida: el solver devolvió el núcleo mínimo insatisfacible.
            Ajusta el escenario y vuelve a calcular.
          </p>
          <div className="mt-4 flex flex-wrap gap-1.5">
            {core.map((constraint) => (
              <Badge key={constraint} tone="danger" className="font-mono">
                {humanizeConstraint(constraint)}
              </Badge>
            ))}
          </div>
        </div>
      </div>
    </DashCard>
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
      className="rounded-[var(--radius-control)] border border-dash-border px-3.5 py-3 shadow-[var(--elev-2)]"
      style={{ backgroundColor: CHART.tooltipBg }}
    >
      <p className="font-mono text-[11px] leading-relaxed text-dash-text-muted">
        {datum.ids.join(" · ")}
      </p>
      <dl className="mt-2.5 grid grid-cols-2 gap-x-5 gap-y-1.5 text-[12px]">
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
      <dd className="tnum font-semibold text-dash-text">{value}</dd>
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
      <Label htmlFor={id} className="!text-dash-text-muted !text-[12px]">
        {label}
      </Label>
      <Input
        id={id}
        value={value}
        placeholder={placeholder}
        inputMode={inputMode}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1.5 rounded-[var(--radius-control)] border-dash-border bg-dash-surface shadow-none focus:border-dash-accent focus:ring-1 focus:ring-dash-accent/25"
      />
    </div>
  );
}

function toDatum(point: FrontierPoint): PointDatum {
  return {
    x: point.objectives.cost,
    y: point.objectives.margin,
    z: 90,
    ids: point.ids,
    availability: point.objectives.availability,
    efficiency: point.objectives.efficiency,
    precio: point.total_price_cop,
  };
}

function sameIds(a: string[], b: string[]): boolean {
  return a.length === b.length && a.every((id, index) => id === b[index]);
}

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
