"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

import { MessageBubble } from "./message-bubble";
import type { ChatMessage, ChatTone } from "./types";

interface MessageListProps {
  messages: ChatMessage[];
  tone?: ChatTone;
  onStreamDone?: (id: string) => void;
  onRetry?: () => void;
  className?: string;
  /** Contenido opcional arriba de la lista (ej. aviso de endpoint pendiente). */
  header?: React.ReactNode;
}

export function MessageList({
  messages,
  tone = "light",
  onStreamDone,
  onRetry,
  className,
  header,
}: MessageListProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);

  const stickToBottom = React.useCallback(() => {
    const node = containerRef.current;
    if (!node) return;
    node.scrollTop = node.scrollHeight;
  }, []);

  React.useEffect(() => {
    stickToBottom();
  }, [messages.length, stickToBottom]);

  return (
    <div
      ref={containerRef}
      className={cn(
        "min-h-0 flex-1 overflow-y-auto scroll-slim",
        tone === "light" && "scroll-slim-light",
        className,
      )}
    >
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-5 px-5 py-8 sm:px-8">
        {header}
        {messages.map((message, index) => (
          <MessageBubble
            key={message.id}
            message={message}
            tone={tone}
            onTick={stickToBottom}
            onStreamDone={onStreamDone}
            onRetry={
              message.status === "error" && index === messages.length - 1 ? onRetry : undefined
            }
          />
        ))}
      </div>
    </div>
  );
}
