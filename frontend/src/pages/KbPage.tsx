import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2, Search, Upload, Edit3, Save, X } from "lucide-react";
import { kbApi } from "@/api/kb";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Textarea, Label } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { formatDate } from "@/lib/utils";
import type { KbDocumentFull } from "@/api/types";

export default function KbPage() {
  const qc = useQueryClient();
  const docsQ = useQuery({ queryKey: ["kb", "list"], queryFn: kbApi.list });
  const removeMut = useMutation({
    mutationFn: (id: string) => kbApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["kb", "list"] }),
  });

  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [tags, setTags] = useState("");
  const uploadMut = useMutation({
    mutationFn: () =>
      kbApi.upload({
        title,
        body,
        source_type: "md",
        category_tags: tags ? tags.split(",").map((s) => s.trim()).filter(Boolean) : undefined,
      }),
    onSuccess: () => {
      setTitle(""); setBody(""); setTags("");
      qc.invalidateQueries({ queryKey: ["kb", "list"] });
    },
  });

  const [q, setQ] = useState("");
  const [searchHits, setSearchHits] = useState<Awaited<ReturnType<typeof kbApi.search>>>([]);
  const searchMut = useMutation({
    mutationFn: () => kbApi.search(q, { top_k: 5 }),
    onSuccess: (hits) => setSearchHits(hits),
  });

  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Knowledge base</h1>
        <p className="text-[13px] text-[color:var(--color-fg-muted)] mt-1">
          Dokumenty w tabeli <code className="text-[color:var(--color-mint)]">kb_chunks</code> (embedding 384-dim, multilingual-e5-small) + tsvector PL.
          Kliknij wiersz / ikonę edycji żeby zobaczyć pełną treść — zmiana body uruchomi re-chunk + re-embed.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-5">
        <Card>
          <CardHeader>
            <CardTitle><Upload className="inline -mt-0.5 mr-1" size={14} /> Wgraj nowy dokument</CardTitle>
          </CardHeader>
          <CardBody className="flex flex-col gap-3">
            <div className="flex flex-col gap-1.5">
              <Label>Tytuł</Label>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="np. Procedura zwrot 101 dni" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Tagi kategorii (CSV)</Label>
              <Input value={tags} onChange={(e) => setTags(e.target.value)} placeholder="refund_request, voucher_redemption" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Treść (markdown)</Label>
              <Textarea value={body} onChange={(e) => setBody(e.target.value)} rows={10} placeholder="# Procedura..." />
            </div>
            <div className="flex items-center gap-3">
              <Button onClick={() => uploadMut.mutate()} disabled={!title || !body || uploadMut.isPending}>
                {uploadMut.isPending ? "Wgrywam + embedduję…" : "Wgraj"}
              </Button>
              {uploadMut.error && <span className="text-[12px] text-[color:var(--color-coral)]">{(uploadMut.error as Error).message}</span>}
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle><Search className="inline -mt-0.5 mr-1" size={14} /> Test retrievera</CardTitle>
          </CardHeader>
          <CardBody className="flex flex-col gap-3">
            <div className="flex gap-2">
              <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="np. czy mogę wymienić voucher na inne przeżycie" />
              <Button variant="secondary" onClick={() => searchMut.mutate()} disabled={!q.trim() || searchMut.isPending}>Szukaj</Button>
            </div>
            <div className="flex flex-col gap-2">
              {searchHits.map((h) => (
                <div key={h.chunk_id} className="px-3 py-2 rounded bg-[color:var(--color-bg-2)] border border-[color:var(--color-line)] text-[12.5px]">
                  <div className="flex items-center justify-between mb-1">
                    <button
                      onClick={() => setSelectedDocId(h.document_id)}
                      className="text-[color:var(--color-fg-muted)] hover:text-[color:var(--color-mint)] underline-offset-2 hover:underline text-left"
                    >
                      {h.document_title}
                    </button>
                    <Badge tone="azure">{(h.relevance ?? 0).toFixed(3)}</Badge>
                  </div>
                  <div className="text-[color:var(--color-fg-dim)] line-clamp-3">{h.content}</div>
                </div>
              ))}
              {searchHits.length === 0 && q && !searchMut.isPending && (
                <div className="text-[12.5px] text-[color:var(--color-fg-dim)]">Wciśnij „Szukaj".</div>
              )}
            </div>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Dokumenty w bazie ({docsQ.data?.length ?? 0})</CardTitle></CardHeader>
        <CardBody>
          {docsQ.isLoading && <div className="text-sm text-[color:var(--color-fg-muted)]">Ładuję…</div>}
          {docsQ.data && docsQ.data.length === 0 && (
            <div className="text-sm text-[color:var(--color-fg-muted)]">Brak dokumentów. Uruchom <code>seed_kb.py</code> albo wgraj ręcznie powyżej.</div>
          )}
          {docsQ.data && docsQ.data.length > 0 && (
            <table className="w-full text-[13px]">
              <thead>
                <tr className="text-left text-[11px] uppercase tracking-wider text-[color:var(--color-fg-muted)]">
                  <th className="py-2 pr-3">Tytuł</th>
                  <th className="py-2 pr-3">Tagi</th>
                  <th className="py-2 pr-3 text-right">Znaki</th>
                  <th className="py-2 pr-3">Wgrany</th>
                  <th className="py-2 pr-0" />
                </tr>
              </thead>
              <tbody>
                {docsQ.data.map((d) => (
                  <tr key={d.id} className="border-t border-[color:var(--color-line)] hover:bg-[color:var(--color-bg-2)]">
                    <td className="py-2 pr-3">
                      <button
                        onClick={() => setSelectedDocId(d.id)}
                        className="font-medium hover:text-[color:var(--color-mint)] text-left"
                      >
                        {d.title}
                      </button>
                    </td>
                    <td className="py-2 pr-3">
                      <div className="flex flex-wrap gap-1">
                        {(d.category_tags || []).map((t) => <Badge key={t} tone="violet">{t}</Badge>)}
                      </div>
                    </td>
                    <td className="py-2 pr-3 tabular text-right text-[color:var(--color-fg-muted)]">{d.char_count}</td>
                    <td className="py-2 pr-3 text-[color:var(--color-fg-dim)]">{formatDate(d.created_at)}</td>
                    <td className="py-2 pr-0 text-right whitespace-nowrap">
                      <Button variant="ghost" size="sm" onClick={() => setSelectedDocId(d.id)} title="Podgląd / edycja">
                        <Edit3 size={14} />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => { if (confirm(`Usunąć "${d.title}"?`)) removeMut.mutate(d.id); }}>
                        <Trash2 size={14} />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardBody>
      </Card>

      {selectedDocId && (
        <DocumentEditor docId={selectedDocId} onClose={() => setSelectedDocId(null)} />
      )}
    </div>
  );
}

function DocumentEditor({ docId, onClose }: { docId: string; onClose: () => void }) {
  const qc = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["kb", "doc", docId],
    queryFn: () => kbApi.get(docId),
  });

  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [tags, setTags] = useState("");
  const [bootstrap, setBootstrap] = useState(false);

  if (data && !bootstrap) {
    setTitle(data.title);
    setBody(data.body_raw);
    setTags((data.category_tags || []).join(", "));
    setBootstrap(true);
  }

  const save = useMutation({
    mutationFn: (doc: KbDocumentFull) =>
      kbApi.update(doc.id, {
        title: title !== doc.title ? title : undefined,
        body: body !== doc.body_raw ? body : undefined,
        category_tags: tags.split(",").map((s) => s.trim()).filter(Boolean),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["kb"] });
      setEditing(false);
    },
  });

  return (
    <div className="fixed inset-0 z-50 bg-black/60 grid place-items-center p-6 overflow-y-auto" onClick={onClose}>
      <div className="bg-[color:var(--color-bg-1)] border border-[color:var(--color-line)] rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 py-4 border-b border-[color:var(--color-line)]">
          <div>
            <h3 className="text-[14px] font-semibold tracking-tight">Knowledge base document</h3>
            {data && (
              <div className="text-[11.5px] text-[color:var(--color-fg-dim)] mt-0.5 font-[family-name:var(--font-mono)]">
                {data.id} · {data.chunk_count} chunks · {data.char_count} chars · updated {formatDate(data.updated_at)}
              </div>
            )}
          </div>
          <button onClick={onClose} className="text-[color:var(--color-fg-muted)] hover:text-[color:var(--color-fg)]">
            <X size={18} />
          </button>
        </div>

        <div className="px-5 py-4">
          {isLoading && <div className="text-sm text-[color:var(--color-fg-muted)]">Ładuję…</div>}
          {error && <div className="text-sm text-[color:var(--color-coral)]">{(error as Error).message}</div>}
          {data && (
            <div className="flex flex-col gap-3">
              <div className="flex flex-col gap-1.5">
                <Label>Tytuł</Label>
                <Input value={title} onChange={(e) => setTitle(e.target.value)} disabled={!editing} />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label>Tagi (CSV)</Label>
                <Input value={tags} onChange={(e) => setTags(e.target.value)} disabled={!editing} />
              </div>
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <Label>Treść (markdown / raw)</Label>
                  {editing && (
                    <span className="text-[11px] text-[color:var(--color-amber)]">Zmiana body → re-chunk + re-embed na zapisie</span>
                  )}
                </div>
                <Textarea value={body} onChange={(e) => setBody(e.target.value)} rows={20} disabled={!editing} />
              </div>

              <div className="flex items-center gap-2 pt-1">
                {!editing && <Button variant="secondary" size="sm" onClick={() => setEditing(true)}><Edit3 size={14} /> Edytuj</Button>}
                {editing && (
                  <>
                    <Button size="sm" onClick={() => save.mutate(data)} disabled={save.isPending}>
                      <Save size={14} /> {save.isPending ? "Zapisuję + reembedduję…" : "Zapisz"}
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => {
                      setEditing(false);
                      setTitle(data.title);
                      setBody(data.body_raw);
                      setTags((data.category_tags || []).join(", "));
                    }}>Anuluj</Button>
                  </>
                )}
                {save.error && (
                  <span className="text-[12px] text-[color:var(--color-coral)]">{(save.error as Error).message}</span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
