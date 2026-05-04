import { api } from "./client";
import type { KbDocument, KbDocumentFull, KbSearchHit } from "./types";

export const kbApi = {
  list: () => api<KbDocument[]>("/api/v1/kb/documents"),
  get: (id: string) => api<KbDocumentFull>(`/api/v1/kb/documents/${id}`),
  upload: (payload: {
    title: string;
    body: string;
    source_type?: string;
    source_url?: string;
    category_tags?: string[];
    metadata?: Record<string, unknown>;
  }) =>
    api<KbDocument>("/api/v1/kb/documents", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  update: (
    id: string,
    payload: { title?: string; body?: string; category_tags?: string[]; source_url?: string },
  ) =>
    api<KbDocumentFull>(`/api/v1/kb/documents/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  remove: (id: string) => api<{ ok: boolean }>(`/api/v1/kb/documents/${id}`, { method: "DELETE" }),
  search: (q: string, opts?: { category?: string; top_k?: number }) => {
    const sp = new URLSearchParams({ q });
    if (opts?.category) sp.set("category", opts.category);
    if (opts?.top_k) sp.set("top_k", String(opts.top_k));
    return api<KbSearchHit[]>(`/api/v1/kb/search?${sp.toString()}`);
  },
};
