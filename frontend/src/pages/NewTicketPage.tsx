import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { ticketsApi } from "@/api/tickets";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Textarea, Label } from "@/components/ui/Input";

export default function NewTicketPage() {
  const navigate = useNavigate();
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [fromEmail, setFromEmail] = useState("");
  const [fromName, setFromName] = useState("");
  const [source, setSource] = useState<"email" | "chat" | "form" | "manual">("manual");

  const submit = useMutation({
    mutationFn: () =>
      ticketsApi.create({
        source,
        sender: { email: fromEmail || null, name: fromName || null },
        subject: subject || null,
        body,
      }),
    onSuccess: (res) => {
      if (res.ticket_id) navigate(`/ticket/${res.ticket_id}`);
    },
  });

  return (
    <div className="max-w-3xl flex flex-col gap-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">New ticket</h1>
        <p className="text-[13px] text-[color:var(--color-fg-muted)] mt-1">
          Wstaw zgłoszenie ręcznie. W produkcji ten endpoint przyjmuje wystawione tickety z Twojego CMS / inboxa przez HMAC-podpisany webhook.
        </p>
      </div>
      <Card>
        <CardHeader><CardTitle>Treść zgłoszenia</CardTitle></CardHeader>
        <CardBody className="grid grid-cols-2 gap-4">
          <div className="col-span-2 grid grid-cols-3 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label>Source</Label>
              <select
                value={source}
                onChange={(e) => setSource(e.target.value as typeof source)}
                className="bg-[color:var(--color-bg-2)] border border-[color:var(--color-line)] rounded-md text-sm h-10 px-3"
              >
                <option value="manual">manual</option>
                <option value="form">form</option>
                <option value="email">email</option>
                <option value="chat">chat</option>
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>From email</Label>
              <Input value={fromEmail} onChange={(e) => setFromEmail(e.target.value)} placeholder="klient@example.com" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>From name</Label>
              <Input value={fromName} onChange={(e) => setFromName(e.target.value)} placeholder="Anna K." />
            </div>
          </div>

          <div className="col-span-2 flex flex-col gap-1.5">
            <Label>Subject</Label>
            <Input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="np. Voucher SPA — pytanie" />
          </div>
          <div className="col-span-2 flex flex-col gap-1.5">
            <Label>Body</Label>
            <Textarea value={body} onChange={(e) => setBody(e.target.value)} rows={10} placeholder="Dzień dobry, dostałam voucher WPRZ-184220..." />
          </div>

          <div className="col-span-2 flex items-center gap-3 pt-1">
            <Button onClick={() => submit.mutate()} disabled={!body.trim() || submit.isPending}>
              {submit.isPending ? "Wysyłam…" : "Wystaw ticket → uruchom pipeline"}
            </Button>
            {submit.error && (
              <span className="text-[12.5px] text-[color:var(--color-coral)]">{(submit.error as Error).message}</span>
            )}
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
