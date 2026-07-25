"use client";

import * as React from "react";
import { Bot, Plus } from "lucide-react";

import { Composer } from "@/components/chat/composer";
import { MessageList } from "@/components/chat/message-list";
import type { ChatMessage } from "@/components/chat/types";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { describeError } from "@/lib/errors";
import { getAdminSessionId, newAdminSessionId } from "@/lib/session";

import { DashCard } from "./dash-ui";

const SUGGESTIONS = [
  "¿Cuál es la oportunidad más grande del histórico?",
  "¿Qué componente tiene el mayor riesgo de inventario?",
  "¿Qué bundle debería crear primero?",
  "¿Qué implica el objetivo activo para el cliente?",
];

function uid(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

/** Copiloto admin: `POST /admin/chat` con tools de BI sobre datos reales del panel. */
export function ViewChatbot() {
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [draft, setDraft] = React.useState("");
  const [busy, setBusy] = React.useState(false);

  const sessionIdRef = React.useRef<string>("");
  const lastMessageRef = React.useRef<string>("");

  const send = React.useCallback(
    async (raw: string) => {
      const text = raw.trim();
      if (!text || busy) return;

      if (!sessionIdRef.current) sessionIdRef.current = getAdminSessionId();
      lastMessageRef.current = text;
      const pendingId = uid();

      setDraft("");
      setMessages((current) => [
        ...current.filter((message) => message.status !== "error"),
        { id: uid(), role: "user", content: text, status: "done" },
        { id: pendingId, role: "assistant", content: "", status: "loading" },
      ]);
      setBusy(true);

      try {
        const { data, simulado } = await api.adminChat({
          message: text,
          session_id: sessionIdRef.current,
        });
        setMessages((current) =>
          current.map((message) =>
            message.id === pendingId
              ? {
                  ...message,
                  content: data.reply,
                  trace: data.trace,
                  status: "streaming",
                  simulado,
                }
              : message,
          ),
        );
      } catch (cause) {
        setMessages((current) =>
          current.map((message) =>
            message.id === pendingId
              ? { ...message, content: describeError(cause), status: "error" }
              : message,
          ),
        );
      } finally {
        setBusy(false);
      }
    },
    [busy],
  );

  const handleStreamDone = React.useCallback((id: string) => {
    setMessages((current) =>
      current.map((message) => (message.id === id ? { ...message, status: "done" } : message)),
    );
  }, []);

  function handleNewChat() {
    sessionIdRef.current = newAdminSessionId();
    lastMessageRef.current = "";
    setMessages([]);
    setDraft("");
    setBusy(false);
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-dash-border px-6 py-5 lg:px-8">
        <h2 className="flex items-center gap-2.5 text-[15px] font-semibold leading-tight text-dash-text">
          <Bot className="size-4 text-dash-accent" strokeWidth={1.75} />
          Chatbot de administración
        </h2>

        <Button variant="dash" size="sm" onClick={handleNewChat} disabled={!messages.length}>
          <Plus className="size-3.5" strokeWidth={2} />
          Nueva conversación
        </Button>
      </div>

      {messages.length ? (
        <MessageList
          messages={messages}
          tone="light"
          onStreamDone={handleStreamDone}
          onRetry={() => void send(lastMessageRef.current)}
        />
      ) : (
        <div className="min-h-0 flex-1 overflow-y-auto scroll-slim">
          <div className="mx-auto w-full max-w-3xl px-6 py-8 lg:px-8">
            <DashCard>
              <p className="text-[13px] leading-relaxed text-dash-text-muted">
                Pregunta sobre oportunidades, inventario u objetivos. Las respuestas usan las tools
                de análisis del backend sobre los mismos datos del dashboard.
              </p>

              <div className="mt-5 flex flex-wrap gap-2">
                {SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => void send(suggestion)}
                    className="rounded-[var(--radius-control)] border border-dash-border bg-dash-surface px-3 py-2 text-left text-[12px] text-dash-text-muted transition-colors duration-150 hover:border-dash-border-strong hover:bg-dash-surface-2 hover:text-dash-text"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </DashCard>
          </div>
        </div>
      )}

      <div className="shrink-0 border-t border-dash-border bg-dash-surface px-6 py-4 lg:px-8">
        <div className="mx-auto w-full max-w-3xl">
          <Composer
            value={draft}
            onChange={setDraft}
            onSubmit={() => void send(draft)}
            busy={busy}
            tone="light"
            quietChrome
            placeholder="Pregunta sobre oportunidades, riesgos de inventario u objetivos…"
            ariaLabel="Mensaje para el copiloto de administración"
          />
          <p className="mt-2 text-center text-[11px] text-dash-text-aux">
            Enter envía · Shift + Enter salta línea
          </p>
        </div>
      </div>
    </div>
  );
}
