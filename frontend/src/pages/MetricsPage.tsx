import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Info } from "lucide-react";
import { metricsApi } from "@/api/metrics";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Stat } from "@/components/ui/Stat";
import { Badge } from "@/components/ui/Badge";
import { formatPLN, formatUSD } from "@/lib/utils";

export default function MetricsPage() {
  const [days, setDays] = useState(7);
  const { data, isLoading } = useQuery({
    queryKey: ["metrics", days],
    queryFn: () => metricsApi.get(days),
    refetchInterval: 10000,
  });

  // Per-ticket cost is misleading at very low ticket counts because
  // cache_creation tokens dominate before cache reads kick in.
  const showColdStartWarning = data && data.tickets_total > 0 && data.tickets_total < 30 && data.cache_hit_rate < 0.3;

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Cost &amp; quality dashboard</h1>
          <p className="text-[13px] text-[color:var(--color-fg-muted)] mt-1">
            Liczone z <code>audit_log</code> (każdy LLM call = wiersz). Live, nie mock — refresh co 10s.
            Source: <code>GET /api/v1/metrics</code> → SQL aggregate over <code>audit_log</code>.
          </p>
        </div>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="bg-[color:var(--color-bg-2)] border border-[color:var(--color-line)] rounded-md text-[13px] h-9 px-3"
        >
          {[1, 7, 14, 30, 90].map((d) => <option key={d} value={d}>last {d}d</option>)}
        </select>
      </div>

      {isLoading && <div className="text-sm text-[color:var(--color-fg-muted)]">Ładuję…</div>}

      {showColdStartWarning && (
        <Card className="border-[color:var(--color-amber)]/40 bg-[color:var(--color-amber)]/5">
          <CardBody className="text-[12.5px] text-[color:var(--color-amber)] flex items-start gap-2">
            <Info size={14} className="mt-0.5 shrink-0" />
            <div>
              <strong>Cold start: {data!.tickets_total} ticket(s), cache hit rate {(data!.cache_hit_rate * 100).toFixed(1)}%.</strong>{" "}
              <span className="text-[color:var(--color-fg-muted)]">
                Per-ticket cost is currently dominated by <code>cache_creation</code> tokens (1.25× input price).
                Once cache fills (~50+ tickets in a 5-minute window), cache_read kicks in at 0.10× and per-ticket cost drops ~10× toward the ~3 grosza forecast.
              </span>
            </div>
          </CardBody>
        </Card>
      )}

      {data && (
        <>
          <div className="grid grid-cols-4 gap-4">
            <Card><CardBody><Stat label="Tickets in window" value={data.tickets_total} hint={`window ${data.window_days}d`} /></CardBody></Card>
            <Card><CardBody><Stat label="AI spend (USD)" value={formatUSD(data.cost_usd_total)} hint="sum of audit_log.cost_usd" emphasize /></CardBody></Card>
            <Card><CardBody><Stat label="≈ PLN" value={formatPLN(data.cost_usd_total)} hint="@3.62 PLN/USD (NBP, May 2026)" /></CardBody></Card>
            <Card><CardBody><Stat label="Avg per ticket" value={formatUSD(data.cost_usd_per_ticket)} hint={`${formatPLN(data.cost_usd_per_ticket)} avg`} /></CardBody></Card>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader><CardTitle>Cache hit rate</CardTitle></CardHeader>
              <CardBody className="flex flex-col gap-3">
                <div className="tabular text-3xl font-semibold text-[color:var(--color-mint)]">{(data.cache_hit_rate * 100).toFixed(1)}%</div>
                <div className="text-[11px] text-[color:var(--color-fg-dim)]">
                  cache_read / (cache_read + cache_creation). Steady-state target ≥ 90%.
                </div>
                <div className="grid grid-cols-2 gap-2 text-[12px] text-[color:var(--color-fg-muted)]">
                  <div className="flex justify-between"><span>Input fresh</span><span className="tabular">{data.tokens.input.toLocaleString("pl-PL")}</span></div>
                  <div className="flex justify-between"><span>Cache read</span><span className="tabular">{data.tokens.cached_input.toLocaleString("pl-PL")}</span></div>
                  <div className="flex justify-between"><span>Cache write</span><span className="tabular">{data.tokens.cache_creation.toLocaleString("pl-PL")}</span></div>
                  <div className="flex justify-between"><span>Output</span><span className="tabular">{data.tokens.output.toLocaleString("pl-PL")}</span></div>
                </div>
              </CardBody>
            </Card>

            <Card>
              <CardHeader><CardTitle>Drafts / accept-without-edit</CardTitle></CardHeader>
              <CardBody className="flex flex-col gap-3">
                <div className="tabular text-3xl font-semibold text-[color:var(--color-mint)]">{(data.drafts.accept_without_edit_rate * 100).toFixed(1)}%</div>
                <div className="text-[11px] text-[color:var(--color-fg-dim)]">
                  accepted / total. Operator clicks Accept / Edit / Reject in ticket detail; counts from <code>drafts.status</code>.
                </div>
                <div className="grid grid-cols-2 gap-2 text-[12px] text-[color:var(--color-fg-muted)]">
                  <div className="flex justify-between"><span>Accepted</span><span className="tabular">{data.drafts.accepted}</span></div>
                  <div className="flex justify-between"><span>Edited</span><span className="tabular">{data.drafts.edited}</span></div>
                  <div className="flex justify-between"><span>Rejected</span><span className="tabular">{data.drafts.rejected}</span></div>
                  <div className="flex justify-between"><span>Total drafts</span><span className="tabular">{data.drafts.total}</span></div>
                </div>
              </CardBody>
            </Card>
          </div>

          <Card>
            <CardHeader><CardTitle>Tickets per category</CardTitle></CardHeader>
            <CardBody className="flex flex-wrap gap-2">
              {Object.entries(data.tickets_by_category).map(([k, v]) => (
                <Badge key={k} tone="violet">{k} <span className="ml-1 text-[color:var(--color-fg)] tabular">{v}</span></Badge>
              ))}
            </CardBody>
          </Card>
        </>
      )}
    </div>
  );
}
