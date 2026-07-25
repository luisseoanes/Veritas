import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 font-medium transition-[background-color,border-color,box-shadow,transform] duration-150 disabled:pointer-events-none disabled:opacity-50 select-none",
  {
    variants: {
      variant: {
        /** CTA de marca. */
        brand:
          "rounded-full bg-brand text-ice hover:bg-brand-dark active:scale-[0.99] shadow-[var(--elev-1)]",
        /** Ghost blanco sobre fondos oscuros (banner, hero, login). */
        ghost:
          "rounded-full border border-[var(--ghost-border)] bg-[var(--ghost-bg)] text-ice backdrop-blur-md hover:bg-[var(--ghost-bg-hover)] active:scale-[0.99]",
        /** Control del dashboard. */
        dash: "rounded-[var(--radius-control)] border border-dash-border bg-dash-surface-2 text-dash-text hover:border-dash-border-strong hover:bg-[color-mix(in_oklab,var(--dash-surface-2),white_6%)]",
        /** Acento del dashboard (acciones primarias del panel). */
        dashAccent:
          "rounded-[var(--radius-control)] bg-dash-accent text-navy-950 font-semibold hover:brightness-110",
        /** Enlace discreto. */
        quiet: "rounded-full text-dash-text-muted hover:text-dash-text",
      },
      size: {
        sm: "h-8 px-3 text-[13px]",
        md: "h-10 px-4 text-sm",
        lg: "h-12 px-6 text-base",
        icon: "size-10 rounded-full p-0",
      },
      uppercase: {
        true: "uppercase tracking-[0.14em] text-[12px] font-normal",
        false: "",
      },
    },
    defaultVariants: { variant: "dash", size: "md", uppercase: false },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, uppercase, type = "button", ...props }, ref) => (
    <button
      ref={ref}
      type={type}
      className={cn(buttonVariants({ variant, size, uppercase }), className)}
      {...props}
    />
  ),
);
Button.displayName = "Button";

export { buttonVariants };
