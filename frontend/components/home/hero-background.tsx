"use client";

import { motion } from "framer-motion";

import { BRAND } from "@/lib/demo";

export type HeroPhase = "idle" | "typing" | "active";

const CROSSFADE = { duration: 1.6, ease: "easeInOut" } as const;

/**
 * Fondo full-bleed en tres fases (§3.6): video (idle) → imagen (typing) →
 * imagen casi transparente sobre el stage claro del chat (active).
 */
export function HeroBackground({ phase }: { phase: HeroPhase }) {
  const isActive = phase === "active";

  return (
    <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden bg-navy-950">
      <motion.div
        className="absolute inset-0 bg-chat-stage"
        initial={false}
        animate={{ opacity: isActive ? 1 : 0 }}
        transition={{ duration: 0.7, ease: "easeInOut" }}
      />

      <motion.video
        className="absolute inset-0 size-full object-cover"
        src={BRAND.heroVideoUrl}
        autoPlay
        muted
        loop
        playsInline
        preload="auto"
        initial={false}
        animate={{ opacity: phase === "idle" ? 1 : 0 }}
        transition={CROSSFADE}
      />

      <motion.img
        className="absolute inset-0 size-full object-cover"
        src={BRAND.heroImageUrl}
        alt=""
        aria-hidden
        initial={false}
        animate={{ opacity: phase === "typing" ? 1 : isActive ? 0.12 : 0 }}
        transition={CROSSFADE}
      />

      <motion.div
        className="absolute inset-0"
        style={{ background: "var(--hero-veil)" }}
        initial={false}
        animate={{ opacity: isActive ? 0 : 1 }}
        transition={{ duration: 0.7, ease: "easeInOut" }}
      />
    </div>
  );
}
