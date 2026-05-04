import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Sparkles, AlertTriangle, ShieldAlert } from "lucide-react";
import { ticketsApi } from "@/api/tickets";
import { Card } from "@/components/ui/Card";
import { CategoryBadge } from "@/components/tickets/CategoryBadge";
import { StatusBadge } from "@/components/tickets/StatusBadge";
import { Button } from "@/components/ui/Button";
import { relativeTime } from "@/lib/utils";

const STATUS_OPTIONS = ["", "drafted", "in_review", "escalated_human", "sent"];
const CATEGORY_OPTIONS = ["", "voucher_redemption", "expired_complaint", "refund_request", "supplier_dispute", "gift_recipient_confusion", "other"];

export default function Inbox() {
  const [status, setStatus] = useState("");
  const [category, setCategory] = useState("");
  const { data, isLoading, error } = useQuery({
    queryKey: ["tickets", status, category],
    queryFn: () => ticketsApi.list({ status: status || undefined, category: category || undefined, limit: 200 }),
    refetchInterval: 5000,
  });

  const summary = useMemo(() => {
    if (!data) return null;
    const total = data.length;
    const escalated = data.filter((t) => t.status === "escalated_human").length;
    const flagged = data.filter((t) => t.suspected_injection).length;
    const drafted = data.filter((t) => t.status === "drafted" || t.status === "in_review").length;
    return { total, escalated, flagged, drafted };
  }, [data]);

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Inbox</h1>
          <p className="text-[13px] text-[color:var(--color-fg-muted)] mt-1">
            Zgłoszenia po klasyfikacji, gotowe do review. Auto-refresh co 5s.
          </p>
        </div>
        <Link to="/inbox/new">
          <Button>+ New ticket</Button>
        </Link>
      </div>

      {summary && (
        <div className="grid grid-cols-4 gap-3">
          <SummaryCard label="Total" value={summary.total} />
          <SummaryCard label="Drafted / Review" value={summary.drafted} accent="mint" />
          <SummaryCard label="Escalated" value={summary.escalated} accent="coral" icon={<AlertTriangle size={14} />} />
          <SummaryCard label="Suspected injection" value={summary.flagged} accent="amber" icon={<ShieldAlert size={14} />} />
        </div>
      )}

      <div className="flex items-center gap-3">
        <Filter label="Status" value={status} onChange={setStatus} options={STATUS_OPTIONS} />
        <Filter label="Category" value={category} onChange={setCategory} options={CATEGORY_OPTIONS} />
      </div>

      <Card>
        {isLoading && <div className="px-5 py-8 text-sm text-[color:var(--color-fg-muted)]">Ładuję…</div>}
        {error && (
          <div className="px-5 py-8 text-sm text-[color:var(--color-coral)]">
            {(error as Error).message}
          </div>
        )}
        {data && data.length === 0 && (
          <div className="px-5 py-8 text-sm text-[color:var(--color-fg-muted)]">Brak zgłoszeń pasujących do filtra.</div>
        )}
        {data && data.length > 0 && (
          <table className="w-full text-[13px]">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wider text-[color:var(--color-fg-muted)]">
                <th className="px-5 py-3 font-medium">Subject / nadawca</th>
                <th className="px-3 py-3 font-medium">Kanał</th>
                <th className="px-3 py-3 font-medium">Kategoria</th>
                <th className="px-3 py-3 font-medium">Confidence</th>
                <th className="px-3 py-3 font-medium">Status</th>
                <th className="px-3 py-3 font-medium">Wpłynęło</th>
                <th className="px-3 py-3" />
              </tr>
            </thead>
            <tbody>
              {data.map((t) => (
                <tr
                  key={t.id}
                  className="border-t border-[color:var(--color-line)] hover:bg-[color:var(--color-bg-2)] transition-colors"
                >
                  <td className="px-5 py-3">
                    <Link to={`/ticket/${t.id}`} className="font-medium hover:text-[color:var(--color-mint)]">
                      {t.subject || "(brak tematu)"}
                    </Link>
                    <div className="text-[12px] text-[color:var(--color-fg-dim)] truncate max-w-md">
                      {t.from_name || t.from_email || "anonim"} · {t.body.slice(0, 90)}{t.body.length > 90 ? "…" : ""}
                    </div>
                  </td>
                  <td className="px-3 py-3 text-[color:var(--color-fg-muted)] capitalize">{t.source}</td>
                  <td className="px-3 py-3">
                    <CategoryBadge category={t.category} />
                    {t.suspected_injection && (
                      <span className="ml-1 inline-flex items-center text-[color:var(--color-amber)]" title="Suspected injection">
                        <ShieldAlert size={12} />
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-3 tabular text-[color:var(--color-fg-muted)]">
                    {t.classifier_confidence != null ? (t.classifier_confidence * 100).toFixed(0) + "%" : "—"}
                  </td>
                  <td className="px-3 py-3"><StatusBadge status={t.status} /></td>
                  <td className="px-3 py-3 text-[color:var(--color-fg-dim)]">{relativeTime(t.received_at)}</td>
                  <td className="px-3 py-3 text-right">
                    <Link to={`/ticket/${t.id}`} className="text-[color:var(--color-mint)] hover:underline text-[12.5px]">
                      Otwórz →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}

function SummaryCard({ label, value, accent, icon }: { label: string; value: number; accent?: "mint" | "coral" | "amber"; icon?: React.ReactNode }) {
  const accentClass =
    accent === "mint" ? "text-[color:var(--color-mint)]"
      : accent === "coral" ? "text-[color:var(--color-coral)]"
      : accent === "amber" ? "text-[color:var(--color-amber)]"
      : "text-[color:var(--color-fg)]";
  return (
    <Card className="px-5 py-4 flex flex-col gap-1">
      <div className="flex items-center gap-2 text-[11px] uppercase tracking-wider text-[color:var(--color-fg-muted)]">
        {icon ?? <Sparkles size={12} className="text-[color:var(--color-mint)]" />}
        {label}
      </div>
      <div className={"tabular text-2xl font-semibold tracking-tight " + accentClass}>{value}</div>
    </Card>
  );
}

function Filter({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: string[] }) {
  return (
    <label className="flex items-center gap-2">
      <span className="text-[11px] uppercase tracking-wider text-[color:var(--color-fg-muted)]">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="bg-[color:var(--color-bg-2)] border border-[color:var(--color-line)] rounded-md text-[13px] h-9 px-2 focus:outline-none focus:border-[color:var(--color-mint)]"
      >
        {options.map((o) => (
          <option key={o} value={o}>{o || "all"}</option>
        ))}
      </select>
    </label>
  );
}
