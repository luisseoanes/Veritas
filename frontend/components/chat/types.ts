import type { TraceStep } from "@/lib/api/types";

export type ChatMessageStatus = "loading" | "streaming" | "done" | "error";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  status: ChatMessageStatus;
  trace?: TraceStep[];
  /** Marca visible cuando la respuesta la fabricó el front (endpoint pendiente). */
  simulado?: boolean;
}

export type ChatTone = "light" | "dark";
