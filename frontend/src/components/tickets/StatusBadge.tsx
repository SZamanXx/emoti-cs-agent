import { Badge } from "@/components/ui/Badge";
import type { TicketStatus } from "@/api/types";

const labels: Record<string, string> = {
  received: "Odebrany",
  classified: "Sklasyfikowany",
  drafted: "Draft gotowy",
  in_review: "W review",
  approved: "Zaakceptowany",
  edited: "Edytowany",
  rejected: "Odrzucony",
  sent: "Wysłany",
  closed: "Zamknięty",
  escalated_human: "Eskalacja",
};

const tones: Record<string, "mint" | "amber" | "coral" | "azure" | "violet" | "neutral"> = {
  received: "neutral",
  classified: "azure",
  drafted: "mint",
  in_review: "amber",
  approved: "mint",
  edited: "violet",
  rejected: "coral",
  sent: "mint",
  closed: "neutral",
  escalated_human: "coral",
};

export function StatusBadge({ status }: { status: TicketStatus | string }) {
  return <Badge tone={tones[status] || "neutral"}>{labels[status] || status}</Badge>;
}
