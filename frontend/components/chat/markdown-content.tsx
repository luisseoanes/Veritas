"use client";

import * as React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { cn } from "@/lib/utils";

import type { ChatTone } from "./types";

interface MarkdownContentProps {
  children: string;
  tone?: ChatTone;
  className?: string;
}

/** Renderiza respuestas del asistente con Markdown (GFM). No toca el backend. */
export function MarkdownContent({ children, tone = "light", className }: MarkdownContentProps) {
  const light = tone === "light";

  return (
    <div
      className={cn(
        "chat-md text-[15px] leading-relaxed",
        light ? "text-chat-assistant-text" : "text-dash-text",
        className,
      )}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children: node }) => <p className="mb-3 last:mb-0">{node}</p>,
          ul: ({ children: node }) => (
            <ul className="mb-3 list-disc space-y-1 pl-5 last:mb-0">{node}</ul>
          ),
          ol: ({ children: node }) => (
            <ol className="mb-3 list-decimal space-y-1 pl-5 last:mb-0">{node}</ol>
          ),
          li: ({ children: node }) => <li className="leading-relaxed">{node}</li>,
          strong: ({ children: node }) => <strong className="font-semibold">{node}</strong>,
          em: ({ children: node }) => <em className="italic">{node}</em>,
          a: ({ href, children: node }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className={cn(
                "underline underline-offset-2",
                light ? "text-chat-accent" : "text-dash-accent",
              )}
            >
              {node}
            </a>
          ),
          code: ({ className: codeClass, children: node, ...props }) => {
            const inline = !codeClass;
            if (inline) {
              return (
                <code
                  className={cn(
                    "rounded px-1 py-0.5 font-mono text-[13px]",
                    light ? "bg-chat-trace text-chat-text" : "bg-dash-surface-2 text-dash-text",
                  )}
                  {...props}
                >
                  {node}
                </code>
              );
            }
            return (
              <code className={cn("font-mono text-[13px]", codeClass)} {...props}>
                {node}
              </code>
            );
          },
          pre: ({ children: node }) => (
            <pre
              className={cn(
                "mb-3 overflow-x-auto rounded-[var(--radius-control)] p-3 font-mono text-[12px] leading-relaxed last:mb-0",
                light ? "bg-chat-trace text-chat-text" : "bg-dash-surface-2 text-dash-text",
              )}
            >
              {node}
            </pre>
          ),
          h1: ({ children: node }) => (
            <h1 className="mb-2 text-[1.25rem] font-semibold tracking-tight">{node}</h1>
          ),
          h2: ({ children: node }) => (
            <h2 className="mb-2 text-[1.1rem] font-semibold tracking-tight">{node}</h2>
          ),
          h3: ({ children: node }) => (
            <h3 className="mb-2 text-[1rem] font-semibold tracking-tight">{node}</h3>
          ),
          blockquote: ({ children: node }) => (
            <blockquote
              className={cn(
                "mb-3 border-l-2 pl-3 last:mb-0",
                light
                  ? "border-chat-assistant-border text-chat-text-muted"
                  : "border-dash-border text-dash-text-muted",
              )}
            >
              {node}
            </blockquote>
          ),
          table: ({ children: node }) => (
            <div className="mb-3 overflow-x-auto last:mb-0">
              <table className="w-full border-collapse text-[13px]">{node}</table>
            </div>
          ),
          th: ({ children: node }) => (
            <th
              className={cn(
                "border px-2 py-1.5 text-left font-semibold",
                light ? "border-chat-assistant-border" : "border-dash-border",
              )}
            >
              {node}
            </th>
          ),
          td: ({ children: node }) => (
            <td
              className={cn(
                "border px-2 py-1.5",
                light ? "border-chat-assistant-border" : "border-dash-border",
              )}
            >
              {node}
            </td>
          ),
          hr: () => (
            <hr
              className={cn(
                "my-4 border-0 border-t",
                light ? "border-chat-assistant-border" : "border-dash-border",
              )}
            />
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
