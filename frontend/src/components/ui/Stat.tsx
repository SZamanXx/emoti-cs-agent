import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface StatProps {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  className?: string;
  emphasize?: boolean;
}

export function Stat({ label, value, hint, className, emphasize }: StatProps) {
  return (
    <div className={cn("flex flex-col gap-1", className)}>
      <span className="text-[11px] uppercase tracking-wider text-[color:var(--color-fg-muted)]">{label}</span>
      <span
        className={cn(
          "tabular text-2xl font-semibold tracking-tight",
          emphasize ? "text-[color:var(--color-mint)]" : "text-[color:var(--color-fg)]"
        )}
      >
        {value}
      </span>
      {hint && <span className="text-[12px] text-[color:var(--color-fg-dim)]">{hint}</span>}
    </div>
  );
}
