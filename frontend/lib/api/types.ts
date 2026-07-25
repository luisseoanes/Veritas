/**
 * Contratos de datos del backend (`app/main.py`).
 *
 * Regla: si hay conflicto entre estética y estos tipos, ganan los tipos.
 * Los mocks de `mocks/` implementan exactamente estas mismas formas.
 */

export type ObjectiveKey = "balanced" | "customer_value" | "maximize_margin" | "clear_inventory";

export const OBJECTIVE_KEYS: ObjectiveKey[] = [
  "balanced",
  "customer_value",
  "maximize_margin",
  "clear_inventory",
];

/** Los pesos varían por objetivo: no todos declaran las cuatro dimensiones. */
export type ObjectiveWeights = Partial<Record<"cost" | "efficiency" | "availability" | "margin", number>>;

// ------------------------------------------------------------------ GET /health

export interface HealthResponse {
  status: string;
  brand: string;
  llm_provider: "mock" | "gemini" | string;
  graph: Record<string, unknown>;
  eventos_registrados: number;
  objetivo_activo: string;
}

// ------------------------------------------------------- POST /chat · GET /trace

export interface TraceStep {
  step: number;
  kind: "llm" | "tool" | string;
  /** `provider/text/tool_calls` para `llm`; `name/arguments/result` para `tool`. */
  detail: Record<string, unknown>;
  timestamp: string;
}

export interface KnownRequirements {
  power_kw?: number;
  voltage?: number;
  budget_cop?: number;
  features?: string[];
  [key: string]: unknown;
}

export interface ChatRequest {
  message: string;
  session_id: string;
}

export interface ChatResponse {
  session_id: string;
  reply: string;
  business_objective: string;
  trace: TraceStep[];
  known_requirements: KnownRequirements;
}

export interface TraceResponse {
  session_id: string;
  steps: TraceStep[];
}

// ----------------------------------------------------------- GET /admin/verify

export interface VerifyResponse {
  ok: boolean;
}

// -------------------------------------------------------- GET /admin/dashboard

export interface DashboardAssumptions {
  tasa_conversion_asumida: number;
  umbral_co_ocurrencia_bundle: number;
  nota: string;
}

export type UnmetDemandNature = "brecha_de_precio" | "brecha_de_producto" | string;

export interface UnmetDemand {
  tipo: string;
  naturaleza: UnmetDemandNature;
  clientes_afectados: number;
  restriccion_causante: string[];
  perfil: { power_kw?: number; voltage?: number; [key: string]: unknown };
  presupuesto_promedio_cop: number;
  minimo_viable_cop: number;
  brecha_cop: number;
  demanda_direccionable_cop: number;
  formula: string;
  recomendacion: string;
}

export interface BundleGap {
  tipo: string;
  componentes: string[];
  nombres: string[];
  co_ocurrencias: number;
  margen_combinado_cop: number;
  impacto_estimado_cop: number;
  formula: string;
  recomendacion: string;
}

export interface InventoryRisk {
  tipo: string;
  componente: string;
  nombre: string;
  stock: number;
  unica_opcion_para: number;
  veces_recomendado: number;
  indice_riesgo: number;
  exposicion_cop: number;
  formula: string;
  recomendacion: string;
}

export interface DashboardSummary {
  conversaciones_totales: number;
  resueltas: number;
  sin_solucion: number;
  objetivo_activo: string;
}

export interface DashboardResponse {
  supuestos: DashboardAssumptions;
  demanda_no_satisfecha: UnmetDemand[];
  brechas_de_bundle: BundleGap[];
  riesgo_de_inventario: InventoryRisk[];
  eventos_analizados: number;
  resumen: DashboardSummary;
}

// ------------------------------- GET /admin/objectives · POST /admin/objective

export interface ObjectiveOption {
  clave: string;
  etiqueta: string;
  pesos: ObjectiveWeights;
}

export interface ObjectivesResponse {
  activo: string;
  disponibles: ObjectiveOption[];
  garantia: string;
}

export interface SetObjectiveResponse {
  activo: string;
  etiqueta: string;
  pesos: ObjectiveWeights;
}

// ------------------------------------------ POST /solve · POST /admin/frontier

export interface SolveRequest {
  power_kw?: number;
  voltage?: number;
  budget_cop?: number;
  features?: string[];
  require_stock?: boolean;
}

export interface FrontierObjectives {
  cost: number;
  margin: number;
  availability: number;
  efficiency: number;
}

export interface FrontierPoint {
  ids: string[];
  objectives: FrontierObjectives;
  total_price_cop: number;
  total_margin_cop?: number;
  min_stock?: number;
}

export interface ChosenConfiguration {
  ids: string[];
  precio_cop: number;
}

export interface FrontierOk {
  status: "OK";
  frontera: FrontierPoint[];
  dominadas: FrontierPoint[];
  elegida_por_objetivo: Record<string, ChosenConfiguration>;
}

export interface FrontierUnsat {
  status: "SIN_SOLUCION";
  nucleo_insatisfacible: string[];
}

export type FrontierResponse = FrontierOk | FrontierUnsat;

export function isFrontierOk(response: FrontierResponse): response is FrontierOk {
  return response.status === "OK";
}

// ------------------------------------------------------------ POST /demo/reset

export interface DemoResetRequest {
  keep_history: boolean;
}

export interface DemoResetResponse {
  status: string;
  /** Nombre real en `app/main.py` (no `history_conservado`). */
  historico_conservado: boolean;
  objetivo_activo?: string;
  eventos_registrados?: number;
}

// ---------------------------------------------- POST /admin/chat (perfil ADMIN)

/** Espejo de `/chat` + header `X-Admin-Token`. Tools de BI, sin contaminar el log. */
export interface AdminChatRequest {
  message: string;
  session_id: string;
}

export interface AdminChatResponse {
  session_id: string;
  reply: string;
  trace?: TraceStep[];
  business_objective?: string;
  known_requirements?: KnownRequirements;
}

// ---------------------------------------------------------- simulador
// `POST /admin/simulate`: contrafactual sobre las ventas perdidas reales.

export interface SimulateRequest {
  power_kw: number;
  voltage: number;
  price_cop: number;
  kind?: "motor" | "drive" | "protection" | "cable";
  features?: string[];
}

/** Presente solo si un producto NO puede formar configuración válida. */
export interface ViabilityDiagnosis {
  producto: string;
  utilizable: false;
  motivo: "SIN_COMPATIBLES" | "COMPAÑEROS_INCOMPATIBLES";
  explicacion: string;
  para_cerrar_la_brecha?: string;
  slots_en_conflicto?: string[];
  slots_sin_opcion?: string[];
}

export interface SimulatedProfile {
  clientes: number;
  perfil: {
    power_kw: number | null;
    voltage: number | null;
    features: string[];
    presupuesto_cop: number | null;
  };
  presupuesto_promedio_cop: number | null;
  valor_recuperable_cop?: number;
  sigue_bloqueado_por?: string[];
}

export interface SimulateResponse {
  status: "OK" | "SIN_HISTORICO";
  nota?: string;
  productos_simulados?: Array<{
    id: string;
    tipo: string;
    precio_cop: number;
    atributos: Record<string, unknown>;
  }>;
  diagnostico_de_viabilidad?: ViabilityDiagnosis[] | null;
  consultas_perdidas_analizadas?: number;
  perfiles_distintos?: number;
  clientes_recuperados?: number;
  clientes_que_siguen_sin_solucion?: number;
  tasa_de_recuperacion?: number;
  valor_recuperable_cop?: number;
  formula?: string;
  metodo?: string;
  detalle_recuperados?: SimulatedProfile[];
  detalle_no_recuperados?: SimulatedProfile[];
}
