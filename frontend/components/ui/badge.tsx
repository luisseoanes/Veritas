import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-[12px] font-medium leading-none whitespace-nowrap",
  {
    variants: {
      tone: {
        neutral: "border-dash-border bg-dash-surface-2 text-dash-text-muted",
        accent: "border-transparent bg-[var(--dash-accent-soft)] text-dash-accent",
        ok: "border-transparent bg-[var(--dash-ok-soft)] text-dash-ok",
        warn: "border-transparent bg-[var(--dash-warn-soft)] text-dash-warn",
        danger: "border-transparent bg-[var(--dash-danger-soft)] text-dash-danger",
        onDark: "border-[var(--ghost-border)] bg-[var(--ghost-bg)] text-ice backdrop-blur-md",
      },
      size: {
        sm: "px-2.5 py-0.5 text-[11px]",
        md: "",
        lg: "px-4 py-1.5 text-[13px]",
      },
    },
    defaultVariants: { tone: "neutral", size: "md" },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, tone, size, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ tone, size }), className)} {...props} />;
}

export { badgeVariants };
