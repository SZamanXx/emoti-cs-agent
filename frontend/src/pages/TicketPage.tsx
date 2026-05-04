import { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ShieldAlert, AlertTriangle, Send, Edit3, Check, X, Sparkles } from "lucide-react";
import { ticketsApi } from "@/api/tickets";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Textarea } from "@/components/ui/Input";
import { CategoryBadge } from "@/components/tickets/CategoryBadge";
import { StatusBadge } from "@/components/tickets/StatusBadge";
import { PipelineTimeline } from "@/components/tickets/PipelineTimeline";
import { formatDate, formatPLN, formatUSD } from "@/lib/utils";

export default function TicketPage() {
  const { id = "" } = useParams();
  const qc = useQueryClient();
  const ticketQ = useQuery({ queryKey: ["ticket", id], queryFn: () => ticketsApi.get(id), refetchInterval: 4000 });
  const draftQ = useQuery({ queryKey: ["ticket", id, "draft"], queryFn: () => ticketsApi.getDraft(id), refetchInterval: 4000 });

  const [editMode, setEditMode] = useState(false);
  const [editedBody, setEditedBody] = useState("");

  useEffect(() => {
    if (draftQ.data && !editMode) setEditedBody(draftQ.data.edited_body || draftQ.data.body_text);
  }, [draftQ.data, editMode]);

  const reviewMut = useMutation({
    mutationFn: (action: "accept" | "edit" | "reject") =>
      ticketsApi.review(id, action, action === "edit" ? { edited_body: editedBody, reviewed_by: "operator" } : { reviewed_by: "operator" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ticket", id] });
      qc.invalidateQueries({ queryKey: ["ticket", id, "draft"] });
      setEditMode(false);
    },
  });

  const sendMut = useMutation({
    mutationFn: () => ticketsApi.send(id, { approved_by: "operator" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ticket", id] });
      qc.invalidateQueries({ queryKey: ["ticket", id, "draft"] });
    },
  });

  const ticket = ticketQ.data;
  const draft = draftQ.data;

  const canSend = useMemo(() => draft && (draft.status === "accepted" || draft.status === "edited"), [draft]);

  return (
    <div className="flex flex-col gap-5">
      <div>
        <Link to="/inbox" className="inline-flex items-center gap-1 text-[12px] text-[color:var(--color-fg-muted)] hover:text-[color:var(--color-fg)]">
          <ArrowLeft size={14} /> Inbox
        </Link>
      </div>

      {ticketQ.isLoading && <div className="text-sm text-[color:var(--color-fg-muted)]">Ładuję…</div>}
      {ticketQ.error && <div className="text-sm text-[color:var(--color-coral)]">{(ticketQ.error as Error).message}</div>}

      {ticket && (
        <div className="grid grid-cols-[1.4fr_1fr] gap-5">
          {/* Left column — ticket */}
          <div className="flex flex-col gap-4">
            <Card>
              <CardHeader className="flex items-center justify-between">
                <div>
                  <CardTitle>{ticket.subject || "(brak tematu)"}</CardTitle>
                  <div className="mt-1 text-[12px] text-[color:var(--color-fg-muted)]">
                    {ticket.from_name || ticket.from_email || "anonim"} · {ticket.source} · {formatDate(ticket.received_at)}
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <StatusBadge status={ticket.status} />
                  <CategoryBadge category={ticket.category} />
                </div>
              </CardHeader>
              <CardBody>
                {ticket.suspected_injection && (
                  <div className="mb-3 flex items-start gap-2 px-3 py-2 rounded border border-[color:var(--color-amber)]/40 bg-[color:var(--color-amber)]/10 text-[color:var(--color-amber)] text-[12.5px]">
                    <ShieldAlert size={14} className="mt-0.5" />
                    <div>
                      <div className="font-medium">Suspected prompt injection.</div>
                      <div className="text-[color:var(--color-fg-muted)] mt-0.5">
                        Sygnały: {Object.values((ticket.injection_signals || {}) as Record<string, unknown>).flat().slice(0, 6).join(", ") || "—"}
                      </div>
                    </div>
                  </div>
                )}
                <p className="prose-tight">{ticket.body}</p>
                {ticket.classifier_reasoning && (
                  <div className="mt-4 px-3 py-2 rounded bg-[color:var(--color-bg-2)] border border-[color:var(--color-line)] text-[12.5px] text-[color:var(--color-fg-muted)]">
                    <div className="text-[11px] uppercase tracking-wider text-[color:var(--color-fg-dim)] mb-1">Classifier reasoning</div>
                    {ticket.classifier_reasoning}
                  </div>
                )}
              </CardBody>
            </Card>

            <Card>
              <CardHeader><CardTitle>Draft (AI)</CardTitle></CardHeader>
              <CardBody>
                {!draft && <div className="text-sm text-[color:var(--color-fg-muted)]">Brak draftu — albo trwa generowanie, albo ticket został eskalowany do human queue.</div>}
                {draft && (
                  <div className="flex flex-col gap-3">
                    <div className="flex flex-wrap items-center gap-2 text-[12px] text-[color:var(--color-fg-muted)]">
                      <Badge tone="azure">{draft.model_name}</Badge>
                      <Badge tone="violet">prompt {draft.prompt_version}</Badge>
                      <Badge tone={draft.confidence > 0.7 ? "mint" : draft.confidence > 0.4 ? "amber" : "coral"}>
                        confidence {(draft.confidence * 100).toFixed(0)}%
                      </Badge>
                      {draft.requires_action && (
                        <Badge tone="amber"><AlertTriangle size={11} /> requires action: {draft.action_type || "yes"}</Badge>
                      )}
                      <Badge>status: {draft.status}</Badge>
                    </div>

                    {(draft.warnings && draft.warnings.length > 0) && (
                      <div className="px-3 py-2 rounded border border-[color:var(--color-amber)]/40 bg-[color:var(--color-amber)]/10 text-[12.5px] text-[color:var(--color-amber)]">
                        <div className="font-medium mb-1">Warnings</div>
                        <ul className="list-disc list-inside text-[color:var(--color-fg-muted)]">
                          {draft.warnings.map((w, i) => <li key={i}>{w}</li>)}
                        </ul>
                      </div>
                    )}

                    {draft.subject && (
                      <div>
                        <div className="text-[11px] uppercase tracking-wider text-[color:var(--color-fg-muted)] mb-1">Subject</div>
                        <div className="text-[13px]">{draft.subject}</div>
                      </div>
                    )}

                    <div>
                      <div className="text-[11px] uppercase tracking-wider text-[color:var(--color-fg-muted)] mb-1">Body</div>
                      {editMode ? (
                        <Textarea value={editedBody} onChange={(e) => setEditedBody(e.target.value)} rows={14} />
                      ) : (
                        <div className="prose-tight px-3 py-3 rounded bg-[color:var(--color-bg-2)] border border-[color:var(--color-line)]">
                          {draft.edited_body || draft.body_text}
                        </div>
                      )}
                    </div>

                    {draft.citations && draft.citations.length > 0 && (
                      <div>
                        <div className="text-[11px] uppercase tracking-wider text-[color:var(--color-fg-muted)] mb-1">Citations</div>
                        <div className="flex flex-col gap-1.5">
                          {draft.citations.map((c) => (
                            <div key={c.chunk_id} className="px-3 py-2 rounded bg-[color:var(--color-bg-2)] border border-[color:var(--color-line)] text-[12.5px]">
                              <div className="text-[color:var(--color-fg-muted)] mb-1">{c.document_title || "—"} · {c.chunk_id}</div>
                              <div className="text-[color:var(--color-fg-dim)]">{c.snippet}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="flex flex-wrap gap-2 pt-2">
                      {!editMode && draft.status === "draft" && (
                        <>
                          <Button variant="success" size="sm" onClick={() => reviewMut.mutate("accept")}>
                            <Check size={14} /> Accept
                          </Button>
                          <Button variant="secondary" size="sm" onClick={() => setEditMode(true)}>
                            <Edit3 size={14} /> Edit
                          </Button>
                          <Button variant="danger" size="sm" onClick={() => reviewMut.mutate("reject")}>
                            <X size={14} /> Reject
                          </Button>
                        </>
                      )}
                      {editMode && (
                        <>
                          <Button variant="success" size="sm" onClick={() => reviewMut.mutate("edit")}>
                            <Check size={14} /> Save edit
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => { setEditMode(false); setEditedBody(draft.body_text); }}>Cancel</Button>
                        </>
                      )}
                      {canSend && (
                        <Button size="sm" onClick={() => sendMut.mutate()}>
                          <Send size={14} /> Send
                        </Button>
                      )}
                    </div>
                  </div>
                )}
              </CardBody>
            </Card>
          </div>

          {/* Right column — meta */}
          <div className="flex flex-col gap-4">
            <Card>
              <CardHeader><CardTitle>Ticket meta</CardTitle></CardHeader>
              <CardBody className="text-[13px]">
                <KV k="ID" v={ticket.id} mono />
                <KV k="Channel" v={ticket.source} />
                {ticket.channel_thread_id && <KV k="Thread ID" v={ticket.channel_thread_id} mono />}
                <KV k="Recipient" v={ticket.from_email || "—"} />
                <KV k="Język" v={(ticket as { language_hint?: string }).language_hint || "pl"} />
                <KV k="Received" v={formatDate(ticket.received_at)} />
                <KV k="Updated" v={formatDate(ticket.updated_at)} />
              </CardBody>
            </Card>

            {draft && (
              <Card>
                <CardHeader><CardTitle>Cost (this draft)</CardTitle></CardHeader>
                <CardBody>
                  <div className="grid grid-cols-2 gap-3 text-[13px]">
                    <KV k="Input tok." v={draft.input_tokens} />
                    <KV k="Cached" v={draft.cached_input_tokens} />
                    <KV k="Output tok." v={draft.output_tokens} />
                    <KV k="USD" v={formatUSD(draft.cost_usd)} />
                    <KV k="PLN ≈" v={formatPLN(draft.cost_usd)} />
                  </div>
                </CardBody>
              </Card>
            )}

            {ticket.metadata && (
              <Card>
                <CardHeader><CardTitle>Eval expected (sample data)</CardTitle></CardHeader>
                <CardBody className="text-[13px]">
                  {Object.entries(ticket.metadata).map(([k, v]) => (
                    <KV key={k} k={k} v={typeof v === "string" ? v : JSON.stringify(v)} />
                  ))}
                </CardBody>
              </Card>
            )}

            <Card>
              <CardHeader><CardTitle><Sparkles className="inline -mt-0.5 mr-1" size={14} /> Pipeline progress</CardTitle></CardHeader>
              <CardBody>
                <PipelineTimeline ticketId={ticket.id} ticketStatus={ticket.status} />
              </CardBody>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

function KV({ k, v, mono }: { k: string; v: unknown; mono?: boolean }) {
  return (
    <div className="grid grid-cols-[100px_1fr] gap-3 py-1.5 border-b last:border-0 border-[color:var(--color-line)]">
      <div className="text-[11.5px] uppercase tracking-wider text-[color:var(--color-fg-dim)]">{k}</div>
      <div className={mono ? "font-[family-name:var(--font-mono)] text-[12px] text-[color:var(--color-fg-muted)] break-all" : "text-[color:var(--color-fg)] break-words"}>
        {String(v ?? "—")}
      </div>
    </div>
  );
}
