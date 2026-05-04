import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Tone = "neutral" | "mint" | "amber" | "coral" | "violet" | "azure";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

const toneClasses: Record<Tone, string> = {
  neutral:
    "bg-[color:var(--color-bg-3)] text-[color:var(--color-fg-muted)] border border-[color:var(--color-line)]",
  mint: "bg-[color:var(--color-mint)]/15 text-[color:var(--color-mint)] border border-[color:var(--color-mint)]/30",
  amber:
    "bg-[color:var(--color-amber)]/15 text-[color:var(--color-amber)] border border-[color:var(--color-amber)]/30",
  coral:
    "bg-[color:var(--color-coral)]/15 text-[color:var(--color-coral)] border border-[color:var(--color-coral)]/30",
  violet:
    "bg-[color:var(--color-violet)]/15 text-[color:var(--color-violet)] border border-[color:var(--color-violet)]/30",
  azure:
    "bg-[color:var(--color-azure)]/15 text-[color:var(--color-azure)] border border-[color:var(--color-azure)]/30",
};

export function Badge({ tone = "neutral", className, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-[2px] rounded text-[11px] font-medium uppercase tracking-wider",
        toneClasses[tone],
        className
      )}
      {...props}
    />
  );
}
