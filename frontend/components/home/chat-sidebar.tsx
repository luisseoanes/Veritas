"use client";

import { motion } from "framer-motion";
import { MessageSquare, Plus } from "lucide-react";

/** Sidebar del chat activo: entra desde la izquierda con spring (§3.6.4). */
export function ChatSidebar({ onNewChat }: { onNewChat: () => void }) {
  return (
    <motion.aside
      initial={{ x: -72, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: -72, opacity: 0 }}
      transition={{ type: "spring", stiffness: 260, damping: 28 }}
      className="hidden w-[236px] shrink-0 flex-col gap-2 border-r border-chat-sidebar-border bg-chat-sidebar px-3 py-5 md:flex"
    >
      <button
        type="button"
        onClick={onNewChat}
        className="flex items-center gap-2.5 rounded-full bg-chat-user px-4 py-2.5 text-[14px] font-medium text-chat-user-text transition-colors duration-150 hover:bg-brand-dark"
      >
        <Plus className="size-4" strokeWidth={2} />
        Nuevo chat
      </button>

      <div className="mt-3 flex items-center gap-2.5 rounded-2xl border border-chat-sidebar-border bg-chat-stage-soft px-4 py-2.5 text-[14px] text-chat-text">
        <MessageSquare className="size-4 shrink-0 text-chat-accent" strokeWidth={1.75} />
        Chat actual
      </div>
    </motion.aside>
  );
}
