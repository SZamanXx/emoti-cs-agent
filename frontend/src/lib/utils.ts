import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPLN(usd: number, fxRate = 3.62) {
  const pln = usd * fxRate;
  return new Intl.NumberFormat("pl-PL", { style: "currency", currency: "PLN", maximumFractionDigits: 2 }).format(pln);
}

export function formatUSD(usd: number) {
  return `$${usd.toFixed(4)}`;
}

export function formatDate(iso?: string | null) {
  if (!iso) return "—";
  try {
    return new Intl.DateTimeFormat("pl-PL", {
      year: "numeric",
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function relativeTime(iso?: string | null) {
  if (!iso) return "—";
  const ms = Date.now() - new Date(iso).getTime();
  const s = Math.round(ms / 1000);
  if (s < 60) return `${s}s temu`;
  const m = Math.round(s / 60);
  if (m < 60) return `${m} min temu`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h} h temu`;
  const d = Math.round(h / 24);
  return `${d} d temu`;
}
