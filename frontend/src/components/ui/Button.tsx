import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "success";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

const variantClasses: Record<Variant, string> = {
  primary:
    "bg-[color:var(--color-mint)] text-[#0a0f1c] hover:bg-[color:var(--color-mint-dim)] focus-visible:outline-[color:var(--color-mint)] disabled:bg-[color:var(--color-bg-3)] disabled:text-[color:var(--color-fg-dim)]",
  secondary:
    "bg-[color:var(--color-bg-2)] border border-[color:var(--color-line)] text-[color:var(--color-fg)] hover:bg-[color:var(--color-bg-3)]",
  ghost:
    "bg-transparent text-[color:var(--color-fg-muted)] hover:text-[color:var(--color-fg)] hover:bg-[color:var(--color-bg-2)]",
  danger:
    "bg-[color:var(--color-coral)]/10 border border-[color:var(--color-coral)]/40 text-[color:var(--color-coral)] hover:bg-[color:var(--color-coral)]/20",
  success:
    "bg-[color:var(--color-mint)]/15 border border-[color:var(--color-mint)]/40 text-[color:var(--color-mint)] hover:bg-[color:var(--color-mint)]/25",
};

const sizeClasses: Record<Size, string> = {
  sm: "h-8 px-3 text-[13px]",
  md: "h-10 px-4 text-sm",
  lg: "h-11 px-5 text-[15px]",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", className, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md font-medium tracking-tight transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed",
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      {...props}
    />
  )
);
Button.displayName = "Button";
