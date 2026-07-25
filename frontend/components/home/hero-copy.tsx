"use client";

import { motion } from "framer-motion";

/** Hero idle/typing: una sola composición — kicker, título, frase. Sin cards ni stats. */
export function HeroCopy() {
  return (
    <div className="flex min-h-0 flex-1 items-end justify-center px-5 pb-10 sm:px-8">
      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="w-full max-w-3xl text-center"
      >
        <p className="text-[12px] font-medium uppercase tracking-[0.28em] text-ice/70">
          Accionamientos industriales
        </p>
        <h1 className="mt-5 font-display text-4xl font-medium uppercase leading-[1.08] tracking-[0.02em] text-ice sm:text-5xl lg:text-6xl">
          Cotiza tus necesidades en segundos
        </h1>
        <p className="mx-auto mt-6 max-w-xl text-[15px] leading-relaxed text-ice/80 sm:text-base">
          Describe la aplicación con tus palabras. El asesor traduce la necesidad a restricciones
          técnicas y un solver arma la configuración: nunca una lista de productos sin validar.
        </p>
      </motion.div>
    </div>
  );
}
