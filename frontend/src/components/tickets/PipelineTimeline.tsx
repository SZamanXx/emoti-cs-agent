import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, CheckCircle2, AlertTriangle, ShieldAlert, FileText, Search, Sparkles, FolderInput } from "lucide-react";
import { ticketsApi } from "@/api/tickets";
import type { TicketEvent } from "@/api/types";

interface PipelineTimelineProps {
  ticketId: string;
  ticketStatus: string;
}

const STEP_ICONS: Record<string, typeof Loader2> = {
  pipeline_started: Sparkles,
  pre_filter_done: ShieldAlert,
  pre_filter_flagged: ShieldAlert,
  classify_started: Loader2,
  classify_done: CheckCircle2,
  killswitch_blocked: AlertTriangle,
  auto_escalated: FolderInput,
  kb_retrieval_done: Search,
  drafter_started: Loader2,
  drafted: FileText,
  pipeline_completed: CheckCircle2,
};

const STEP_LABELS: Record<string, string> = {
  pipeline_started: "Pipeline started",
  pre_filter_done: "Pattern pre-filter (regex defense)",
  pre_filter_flagged: "Pre-filter FLAGGED (injection markers)",
  classify_started: "Classifier + judge running (Haiku, parallel)",
  classify_done: "Classifier + judge done",
  killswitch_blocked: "Killswitch active — escalating",
  auto_escalated: "Auto-escalated to human queue",
  kb_retrieval_done: "KB retrieval (pgvector + tsvector PL)",
  drafter_started: "Drafter running (Sonnet, structured output)",
  drafted: "Draft ready",
  pipeline_completed: "Pipeline finished",
  ticket_received: "Ticket received",
};

const RUNNING_STATUSES = new Set(["received", "classified"]);

function fmtPayload(event: TicketEvent): string | null {
  const p = event.payload || {};
  switch (event.event_type) {
    case "pre_filter_done": {
      const sigs = (p.signals as string[]) || [];
      const ms = p.elapsed_ms;
      return `${sigs.length ? `signals: ${sigs.join(", ")}` : "no markers"} · ${ms}ms`;
    }
    case "classify_done":
      return `category: ${p.category}, conf ${(((p.confidence as number) || 0) * 100).toFixed(0)}%, judge_injection=${p.judge_is_injection} · ${p.elapsed_ms}ms · classifier $${((p.classifier_cost_usd as number) ?? 0).toFixed(5)} + judge $${((p.judge_cost_usd as number) ?? 0).toFixed(5)}`;
    case "kb_retrieval_done":
      return `${p.chunks_retrieved} chunks (top: ${p.top_doc || "—"}), voucher=${p.voucher_code || "none"} status=${p.voucher_status || "—"} · ${p.elapsed_ms}ms`;
    case "drafter_started":
      return `model: ${p.model} · category: ${p.category}`;
    case "drafted":
      return `confidence ${(((p.confidence as number) || 0) * 100).toFixed(0)}%, citations: ${p.citations_count}, warnings: ${p.warnings_count} · in:${p.input_tokens}+cached:${p.cached_input_tokens}, out:${p.output_tokens} · $${((p.cost_usd as number) ?? 0).toFixed(5)} · ${p.elapsed_ms}ms`;
    case "auto_escalated":
      return p.reason ? `reason: ${p.reason}` : `category: ${p.category}, policy: ${p.policy}`;
    case "killswitch_blocked":
      return `global=${p.global} drafter=${p.drafter} category=${p.category}`;
    case "pipeline_completed":
      return `${p.status} · total ${p.total_ms}ms${p.draft_id ? ` · draft ${p.draft_id}` : ""}${p.reason ? ` · ${p.reason}` : ""}`;
    case "pipeline_started":
      return `source: ${p.source}`;
    case "ticket_received":
      return null;
    default:
      return null;
  }
}

export function PipelineTimeline({ ticketId, ticketStatus }: PipelineTimelineProps) {
  const isRunning = RUNNING_STATUSES.has(ticketStatus);
  const { data, isLoading } = useQuery({
    queryKey: ["ticket", ticketId, "events"],
    queryFn: () => ticketsApi.getEvents(ticketId),
    refetchInterval: isRunning ? 1500 : 5000,
  });

  const events = useMemo(() => data || [], [data]);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <div className="text-[11px] uppercase tracking-wider text-[color:var(--color-fg-muted)]">Pipeline timeline</div>
        {isRunning && (
          <span className="inline-flex items-center gap-1.5 text-[11px] text-[color:var(--color-mint)]">
            <Loader2 size={11} className="animate-spin" />
            running
          </span>
        )}
      </div>

      {isLoading && events.length === 0 && (
        <div className="text-[12.5px] text-[color:var(--color-fg-muted)]">Ładuję eventy…</div>
      )}

      {!isLoading && events.length === 0 && (
        <div className="text-[12.5px] text-[color:var(--color-fg-muted)]">
          Brak eventów. Pipeline zapisuje progress co kroku.
        </div>
      )}

      <ol className="flex flex-col gap-1.5">
        {events.map((ev, i) => {
          const Icon = STEP_ICONS[ev.event_type] ?? Sparkles;
          const label = STEP_LABELS[ev.event_type] ?? ev.event_type;
          const detail = fmtPayload(ev);
          const isFlag = ev.event_type === "pre_filter_flagged" || ev.event_type === "killswitch_blocked";
          const isEscalated = ev.event_type === "auto_escalated";
          const time = new Date(ev.created_at);
          const hh = time.toLocaleTimeString("pl-PL", { hour12: false });
          return (
            <li
              key={ev.id}
              className={`flex items-start gap-2 px-3 py-2 rounded border text-[12.5px] ${
                isFlag
                  ? "border-[color:var(--color-amber)]/40 bg-[color:var(--color-amber)]/10"
                  : isEscalated
                    ? "border-[color:var(--color-coral)]/40 bg-[color:var(--color-coral)]/10"
                    : "border-[color:var(--color-line)] bg-[color:var(--color-bg-2)]"
              }`}
            >
              <Icon size={13} className="mt-0.5 shrink-0 text-[color:var(--color-mint)]" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{i + 1}. {label}</span>
                  <span className="text-[11px] text-[color:var(--color-fg-dim)]">{hh}</span>
                </div>
                {detail && (
                  <div className="text-[color:var(--color-fg-muted)] font-[family-name:var(--font-mono)] text-[11.5px] mt-0.5 break-words">
                    {detail}
                  </div>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
