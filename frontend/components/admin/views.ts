import { Bot, Lightbulb, ScatterChart, Target, Gauge } from "lucide-react";

/** Una sola fuente para el sidebar y para el parámetro `?view=`. */
export const ADMIN_VIEWS = [
  { key: "resumen", label: "Resumen", icon: Gauge },
  { key: "objetivo", label: "Objetivo", icon: Target },
  { key: "frontera", label: "Frontera", icon: ScatterChart },
  { key: "oportunidades", label: "Oportunidades", icon: Lightbulb },
  { key: "chatbot", label: "Chatbot", icon: Bot },
] as const;

export type AdminView = (typeof ADMIN_VIEWS)[number]["key"];

export const DEFAULT_VIEW: AdminView = "resumen";

export function parseView(value: string | null | undefined): AdminView {
  const match = ADMIN_VIEWS.find((view) => view.key === value);
  return match ? match.key : DEFAULT_VIEW;
}
