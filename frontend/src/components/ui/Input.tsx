import { forwardRef, type InputHTMLAttributes, type TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const baseInput =
  "w-full bg-[color:var(--color-bg-2)] border border-[color:var(--color-line)] rounded-md px-3 text-sm text-[color:var(--color-fg)] placeholder:text-[color:var(--color-fg-dim)] focus:outline-none focus:border-[color:var(--color-mint)] focus:ring-1 focus:ring-[color:var(--color-mint)]/40 transition-colors";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => <input ref={ref} className={cn(baseInput, "h-10", className)} {...props} />
);
Input.displayName = "Input";

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea ref={ref} className={cn(baseInput, "py-2 leading-relaxed font-[family-name:var(--font-mono)] text-[13px]", className)} {...props} />
  )
);
Textarea.displayName = "Textarea";

export function Label({ className, ...props }: React.LabelHTMLAttributes<HTMLLabelElement>) {
  return <label className={cn("text-[12px] uppercase tracking-wider text-[color:var(--color-fg-muted)] font-medium", className)} {...props} />;
}
