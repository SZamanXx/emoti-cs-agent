import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Power, ShieldOff, AlertTriangle } from "lucide-react";
import { settingsApi } from "@/api/settings";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

interface ScopeMeta {
  label: string;
  description: string;
  whenEnabled: string;
  whenDisabled: string;
  tone: "global" | "feature" | "category";
}

const SCOPE_META: Record<string, ScopeMeta> = {
  global: {
    label: "Global pipeline",
    description: "Master switch for the whole AI pipeline.",
    whenEnabled: "All categories run through classifier → drafter → review.",
    whenDisabled: "Every ticket auto-escalates to human. AI never runs.",
    tone: "global",
  },
  "feature:drafter": {
    label: "Drafter (Sonnet 4.6)",
    description: "Generates the actual reply text after classification.",
    whenEnabled: "Sonnet writes drafts for non-escalated categories.",
    whenDisabled: "Pipeline stops at classifier; human writes the reply manually with KB+CMS prefill.",
    tone: "feature",
  },
  "feature:auto_reply": {
    label: "Auto-reply (no human review)",
    description: "Bypass the human review step and send drafts directly.",
    whenEnabled: "Eligible categories with high confidence skip the operator queue.",
    whenDisabled: "Every draft requires explicit Accept/Edit before send. Recommended default.",
    tone: "feature",
  },
  "category:voucher_redemption": {
    label: "Category — voucher_redemption",
    description: 'Tickets like "how to redeem", "code does not work", "WPRZ-..."',
    whenEnabled: "Drafter generates a Polish reply with KB FAQ + redemption SOP.",
    whenDisabled: "Tickets in this category route to human queue with no draft.",
    tone: "category",
  },
  "category:expired_complaint": {
    label: "Category — expired_complaint",
    description: "Tickets about vouchers past 36-month validity.",
    whenEnabled: "Drafter generates an empathetic, regulamin-cited reply.",
    whenDisabled: "Tickets in this category route to human queue with no draft.",
    tone: "category",
  },
  "category:gift_recipient_confusion": {
    label: "Category — gift_recipient_confusion",
    description: "Recipients who got a voucher and don't know what to do.",
    whenEnabled: "Drafter explains the brand + first redemption steps using KB.",
    whenDisabled: "Tickets in this category route to human queue with no draft.",
    tone: "category",
  },
  "category:refund_request": {
    label: "Category — refund_request (HARDCODED OFF)",
    description: "Refund tickets are never drafted by AI — security policy (KB-003).",
    whenEnabled: "(N/A — even with this enabled, pipeline routes refund to human.)",
    whenDisabled: "Tickets escalate to human with CMS context prefill.",
    tone: "category",
  },
  "category:supplier_dispute": {
    label: "Category — supplier_dispute (HARDCODED OFF)",
    description: "Supplier disputes never drafted by AI — KB-004 policy.",
    whenEnabled: "(N/A — pipeline routes to Partnerski team.)",
    whenDisabled: "Tickets escalate to human with KB-004 dispute SOP attached.",
    tone: "category",
  },
};

const PRESET_SCOPES = [
  "global",
  "feature:drafter",
  "feature:auto_reply",
  "category:voucher_redemption",
  "category:expired_complaint",
  "category:gift_recipient_confusion",
  "category:refund_request",
  "category:supplier_dispute",
];

const TONE_BADGE: Record<ScopeMeta["tone"], "azure" | "violet" | "neutral"> = {
  global: "azure",
  feature: "violet",
  category: "neutral",
};

export default function SettingsPage() {
  const qc = useQueryClient();
  const list = useQuery({ queryKey: ["killswitches"], queryFn: settingsApi.list });
  const setMut = useMutation({
    mutationFn: (vars: { scope: string; enabled: boolean; reason?: string }) =>
      settingsApi.set(vars.scope, vars.enabled, vars.reason),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["killswitches"] }),
  });

  const existing = new Map((list.data || []).map((k) => [k.scope, k] as const));
  const allScopes = Array.from(new Set([...PRESET_SCOPES, ...(list.data || []).map((k) => k.scope)]));

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings — killswitches</h1>
        <p className="text-[13px] text-[color:var(--color-fg-muted)] mt-1">
          Każdy scope sterowany niezależnie. Auto-disable włącza się gdy accept-without-edit rate spada &lt;40% / 24h dla tej kategorii.
          ENABLED = AI bierze udział w pipeline; DISABLED = pipeline omija krok i eskaluje do human queue.
        </p>
      </div>

      <Card>
        <CardHeader><CardTitle><Power className="inline -mt-0.5 mr-1" size={14} /> Active killswitches</CardTitle></CardHeader>
        <CardBody className="flex flex-col gap-2">
          {allScopes.map((scope) => {
            const meta = SCOPE_META[scope] || {
              label: scope,
              description: "Custom scope.",
              whenEnabled: "AI step active.",
              whenDisabled: "Step bypassed.",
              tone: "feature" as const,
            };
            const ks = existing.get(scope);
            const enabled = ks ? ks.enabled : true;
            const isHardcoded = scope === "category:refund_request" || scope === "category:supplier_dispute";

            return (
              <div
                key={scope}
                className="flex items-start justify-between gap-4 px-4 py-3 rounded bg-[color:var(--color-bg-2)] border border-[color:var(--color-line)]"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge tone={TONE_BADGE[meta.tone]}>{meta.tone}</Badge>
                    <span className="font-mono text-[12.5px] text-[color:var(--color-fg-muted)]">{scope}</span>
                    {ks?.auto_disabled && (
                      <Badge tone="amber"><AlertTriangle size={10} /> auto-disabled</Badge>
                    )}
                    {isHardcoded && (
                      <Badge tone="coral"><ShieldOff size={10} /> hardcoded policy</Badge>
                    )}
                  </div>
                  <div className="mt-1 text-[13px] font-medium">{meta.label}</div>
                  <div className="mt-0.5 text-[12.5px] text-[color:var(--color-fg-muted)]">{meta.description}</div>
                  <div className="mt-1.5 grid grid-cols-2 gap-3 text-[11.5px]">
                    <div className={enabled ? "text-[color:var(--color-mint)]" : "text-[color:var(--color-fg-dim)]"}>
                      <span className="font-medium uppercase tracking-wider">When ENABLED:</span> {meta.whenEnabled}
                    </div>
                    <div className={!enabled ? "text-[color:var(--color-coral)]" : "text-[color:var(--color-fg-dim)]"}>
                      <span className="font-medium uppercase tracking-wider">When DISABLED:</span> {meta.whenDisabled}
                    </div>
                  </div>
                  {ks?.reason && (
                    <div className="mt-1.5 text-[11.5px] text-[color:var(--color-fg-dim)] italic">
                      reason: {ks.reason}{ks.last_changed_by ? ` · by ${ks.last_changed_by}` : ""}
                    </div>
                  )}
                </div>

                <div className="flex flex-col items-end gap-2 shrink-0">
                  <Badge tone={enabled ? "mint" : "coral"}>{enabled ? "ENABLED" : "DISABLED"}</Badge>
                  <Button
                    size="sm"
                    variant={enabled ? "danger" : "success"}
                    onClick={() =>
                      setMut.mutate({
                        scope,
                        enabled: !enabled,
                        reason: enabled ? "manual disable from UI" : "manual re-enable from UI",
                      })
                    }
                  >
                    {enabled ? "Disable" : "Enable"}
                  </Button>
                </div>
              </div>
            );
          })}
        </CardBody>
      </Card>

      <Card>
        <CardHeader><CardTitle>Auto-reply policy (read-only)</CardTitle></CardHeader>
        <CardBody className="text-[13px] text-[color:var(--color-fg-muted)] space-y-2">
          <p>
            Auto-reply jest <strong className="text-[color:var(--color-coral)]">WYŁĄCZONY</strong> domyślnie. Każdy draft idzie przez human review.
            Włączenie per kategoria wymaga: (a) accept-without-edit &gt;75% przez 2 tygodnie, (b) factual error rate &lt;1%, (c) supervisor sign-off.
          </p>
          <p>
            Kategorie <code>refund_request</code> i <code>supplier_dispute</code> NIGDY nie idą auto-reply ani draft AI — hardcoded w pipeline.py
            (decyzja architectural — patrz JOURNEY.md, sekcja "The refund decision").
          </p>
        </CardBody>
      </Card>
    </div>
  );
}
