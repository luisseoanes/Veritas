import Image from "next/image";
import Link from "next/link";

import { BRAND } from "@/lib/demo";
import { cn } from "@/lib/utils";

interface LogoProps {
  className?: string;
  width?: number;
  height?: number;
  /** El logo siempre navega a `/` (§3.3). Solo el login lo usa como imagen suelta. */
  asLink?: boolean;
}

/** Proporción del asset `public/brand/logo.png` (1280×898). */
export function Logo({ className, width = 128, height = 90, asLink = true }: LogoProps) {
  const image = (
    <Image
      src={BRAND.logoSrc}
      alt="WEG"
      width={width}
      height={height}
      priority
      unoptimized
      className={cn("h-auto w-auto select-none", className)}
    />
  );

  if (!asLink) return image;

  return (
    <Link
      href="/"
      aria-label="Ir al inicio"
      className="inline-flex rounded-[var(--radius-control)] transition-opacity duration-150 hover:opacity-90"
    >
      {image}
    </Link>
  );
}
