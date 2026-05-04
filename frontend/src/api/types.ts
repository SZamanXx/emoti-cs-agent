export type Category =
  | "voucher_redemption"
  | "expired_complaint"
  | "refund_request"
  | "supplier_dispute"
  | "gift_recipient_confusion"
  | "other";

export type TicketStatus =
  | "received"
  | "classified"
  | "drafted"
  | "in_review"
  | "approved"
  | "edited"
  | "rejected"
  | "sent"
  | "closed"
  | "escalated_human";

export interface TicketSummary {
  id: string;
  source: string;
  channel_thread_id: string | null;
  from_name: string | null;
  from_email: string | null;
  subject: string | null;
  body: string;
  category: Category | null;
  classifier_confidence: number | null;
  suspected_injection: boolean;
  status: TicketStatus;
  received_at: string;
  created_at: string;
  updated_at: string;
}

export interface Ticket extends TicketSummary {
  classifier_reasoning: string | null;
  injection_signals: Record<string, unknown> | null;
  metadata: Record<string, unknown> | null;
}

export interface Citation {
  chunk_id: string;
  document_title: string | null;
  snippet: string;
  relevance?: number | null;
}

export interface Draft {
  id: string;
  ticket_id: string;
  version: number;
  subject: string | null;
  body_text: string;
  body_html: string | null;
  recipient: string | null;
  confidence: number;
  requires_action: boolean;
  action_type: string | null;
  action_params: Record<string, unknown> | null;
  citations: Citation[] | null;
  warnings: string[] | null;
  prompt_version: string;
  model_name: string;
  input_tokens: number;
  cached_input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  status: string;
  edited_body: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface Killswitch {
  scope: string;
  enabled: boolean;
  auto_disabled: boolean;
  reason: string | null;
  last_changed_by: string | null;
}

export interface Metrics {
  window_days: number;
  tickets_total: number;
  tickets_by_category: Record<string, number>;
  cost_usd_total: number;
  cost_usd_per_ticket: number;
  cost_pln_total_estimate: number;
  cache_hit_rate: number;
  tokens: {
    input: number;
    cached_input: number;
    cache_creation: number;
    output: number;
  };
  drafts: {
    total: number;
    accepted: number;
    edited: number;
    rejected: number;
    accept_without_edit_rate: number;
  };
}

export interface KbDocument {
  id: string;
  title: string;
  source_type: string;
  source_url: string | null;
  category_tags: string[] | null;
  summary: string | null;
  char_count: number;
  created_at: string;
  updated_at: string;
}

export interface KbSearchHit {
  chunk_id: string;
  document_id: string;
  document_title: string;
  content: string;
  relevance: number;
  category_tags: string[] | null;
}

export interface KbDocumentFull extends KbDocument {
  body_raw: string;
  chunk_count: number;
}

export interface TicketEvent {
  id: string;
  ticket_id: string;
  event_type: string;
  payload: Record<string, unknown> | null;
  actor: string | null;
  created_at: string;
}
