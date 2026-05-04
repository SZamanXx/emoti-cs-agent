import { api } from "./client";
import type { Draft, Ticket, TicketEvent, TicketSummary } from "./types";

export interface CreateTicketIn {
  source: string;
  channel_thread_id?: string | null;
  sender?: { email?: string | null; phone?: string | null; name?: string | null };
  subject?: string | null;
  body: string;
  language_hint?: string;
  metadata?: Record<string, unknown>;
}

export const ticketsApi = {
  list: (params?: { status?: string; category?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    if (params?.category) q.set("category", params.category);
    if (params?.limit) q.set("limit", String(params.limit));
    const qs = q.toString();
    return api<TicketSummary[]>(`/api/v1/tickets${qs ? `?${qs}` : ""}`);
  },

  get: (id: string) => api<Ticket>(`/api/v1/tickets/${id}`),

  getDraft: (id: string) => api<Draft | null>(`/api/v1/tickets/${id}/draft`),

  getEvents: (id: string) => api<TicketEvent[]>(`/api/v1/tickets/${id}/events`),

  create: (payload: CreateTicketIn) =>
    api<{ ticket_id: string; status: string }>(`/api/v1/tickets`, {
      method: "POST",
      headers: { "X-Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify(payload),
    }),

  review: (id: string, action: "accept" | "edit" | "reject", payload?: { edited_body?: string; reason?: string; reviewed_by?: string }) =>
    api<Draft>(`/api/v1/tickets/${id}/review`, {
      method: "POST",
      body: JSON.stringify({ action, ...payload }),
    }),

  send: (id: string, payload?: { approved_by?: string; edits?: string; send_via?: string }) =>
    api<Draft>(`/api/v1/tickets/${id}/send`, {
      method: "POST",
      body: JSON.stringify(payload || {}),
    }),
};
