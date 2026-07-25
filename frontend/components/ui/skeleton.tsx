import { cn } from "@/lib/utils";

/** Shimmer, no spinner genérico (§3.8 motion). */
export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("dash-skeleton", className)} aria-hidden {...props} />;
}
