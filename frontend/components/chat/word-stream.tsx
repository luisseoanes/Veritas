"use client";

import * as React from "react";

interface WordStreamProps {
  text: string;
  /** `false` pinta el texto completo de inmediato (mensajes ya vistos). */
  animate?: boolean;
  speedMs?: number;
  onTick?: () => void;
  onDone?: () => void;
  /** Permite renderizar el tramo revelado (p. ej. Markdown). */
  render?: (visible: string) => React.ReactNode;
}

/** Respuesta del asesor palabra por palabra (~30–40 ms/palabra, §3.6.5). */
export function WordStream({
  text,
  animate = true,
  speedMs = 34,
  onTick,
  onDone,
  render,
}: WordStreamProps) {
  const words = React.useMemo(() => text.split(" "), [text]);
  const [revealed, setRevealed] = React.useState(animate ? 0 : words.length);

  const tickRef = React.useRef(onTick);
  const doneRef = React.useRef(onDone);
  tickRef.current = onTick;
  doneRef.current = onDone;

  React.useEffect(() => {
    if (!animate) {
      setRevealed(words.length);
      return;
    }
    setRevealed(0);
    let current = 0;
    const timer = window.setInterval(() => {
      current += 1;
      setRevealed(current);
      tickRef.current?.();
      if (current >= words.length) {
        window.clearInterval(timer);
        doneRef.current?.();
      }
    }, speedMs);
    return () => window.clearInterval(timer);
  }, [animate, speedMs, words]);

  const visible = words.slice(0, revealed).join(" ");
  if (render) return <>{render(visible)}</>;
  return <span>{visible}</span>;
}
