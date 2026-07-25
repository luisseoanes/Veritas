"use client";

import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";

import { Composer } from "@/components/chat/composer";
import { MessageList } from "@/components/chat/message-list";
import type { ChatMessage } from "@/components/chat/types";
import { api } from "@/lib/api";
import { describeError } from "@/lib/errors";
import { getSessionId, newSessionId } from "@/lib/session";
import { cn } from "@/lib/utils";

import { ChatSidebar } from "./chat-sidebar";
import { HeroBackground, type HeroPhase } from "./hero-background";
import { HeroCopy } from "./hero-copy";

function uid(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export function HomeExperience({ banner }: { banner: React.ReactNode }) {
  const [phase, setPhase] = React.useState<HeroPhase>("idle");
  const [draft, setDraft] = React.useState("");
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [busy, setBusy] = React.useState(false);

  const sessionIdRef = React.useRef<string>("");
  const lastMessageRef = React.useRef<string>("");

  const ensureSession = React.useCallback(() => {
    if (!sessionIdRef.current) sessionIdRef.current = getSessionId();
    return sessionIdRef.current;
  }, []);

  /** Idle ⇄ typing: el fondo reacciona al primer carácter, no al envío. */
  const handleDraftChange = React.useCallback((value: string) => {
    setDraft(value);
    setPhase((current) => {
      if (current === "active") return current;
      return value.trim().length > 0 ? "typing" : "idle";
    });
  }, []);

  const send = React.useCallback(
    async (raw: string) => {
      const text = raw.trim();
      if (!text || busy) return;

      lastMessageRef.current = text;
      const sessionId = ensureSession();
      const pendingId = uid();

      setDraft("");
      setPhase("active");
      setMessages((current) => [
        ...current.filter((message) => message.status !== "error"),
        { id: uid(), role: "user", content: text, status: "done" },
        { id: pendingId, role: "assistant", content: "", status: "loading" },
      ]);
      setBusy(true);

      try {
        const response = await api.chat({ message: text, session_id: sessionId });
        setMessages((current) =>
          current.map((message) =>
            message.id === pendingId
              ? {
                  ...message,
                  content: response.reply,
                  trace: response.trace,
                  status: "streaming",
                }
              : message,
          ),
        );
      } catch (error) {
        setMessages((current) =>
          current.map((message) =>
            message.id === pendingId
              ? { ...message, content: describeError(error), status: "error" }
              : message,
          ),
        );
      } finally {
        setBusy(false);
      }
    },
    [busy, ensureSession],
  );

  const handleStreamDone = React.useCallback((id: string) => {
    setMessages((current) =>
      current.map((message) => (message.id === id ? { ...message, status: "done" } : message)),
    );
  }, []);

  const handleNewChat = React.useCallback(() => {
    sessionIdRef.current = newSessionId();
    lastMessageRef.current = "";
    setMessages([]);
    setDraft("");
    setBusy(false);
    setPhase("idle");
  }, []);

  const isActive = phase === "active";

  return (
    <div className="relative flex h-dvh flex-col overflow-hidden">
      <HeroBackground phase={phase} />
      {banner}

      <main className="flex min-h-0 flex-1">
        <AnimatePresence initial={false}>
          {isActive ? <ChatSidebar key="sidebar" onNewChat={handleNewChat} /> : null}
        </AnimatePresence>

        <div className="flex min-h-0 flex-1 flex-col">
          {isActive ? (
            <MessageList
              messages={messages}
              tone="light"
              onStreamDone={handleStreamDone}
              onRetry={() => send(lastMessageRef.current)}
            />
          ) : (
            <HeroCopy />
          )}

          <motion.div
            layout
            transition={{ type: "spring", stiffness: 210, damping: 28 }}
            className="shrink-0 px-5 pb-7 sm:px-8"
          >
            <div className="mx-auto w-full max-w-3xl">
              <Composer
                value={draft}
                onChange={handleDraftChange}
                onSubmit={() => send(draft)}
                busy={busy}
                tone="light"
                autoFocus
              />
              <p
                className={cn(
                  "mt-3 text-center text-[12px]",
                  isActive ? "text-chat-text-muted" : "text-ice/60",
                )}
              >
                Enter envía · Shift + Enter salta línea
              </p>
            </div>
          </motion.div>

          {isActive ? null : <div className="min-h-0 flex-1" aria-hidden />}
        </div>
      </main>
    </div>
  );
}
