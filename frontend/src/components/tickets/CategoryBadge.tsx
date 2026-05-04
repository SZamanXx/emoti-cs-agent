import { Badge } from "@/components/ui/Badge";
import type { Category } from "@/api/types";

const labels: Record<string, string> = {
  voucher_redemption: "Realizacja",
  expired_complaint: "Wygasły",
  refund_request: "Zwrot",
  supplier_dispute: "Spór z dostawcą",
  gift_recipient_confusion: "Obdarowany",
  other: "Inne",
};

const tones: Record<string, "mint" | "amber" | "coral" | "violet" | "azure" | "neutral"> = {
  voucher_redemption: "azure",
  expired_complaint: "amber",
  refund_request: "coral",
  supplier_dispute: "violet",
  gift_recipient_confusion: "mint",
  other: "neutral",
};

export function CategoryBadge({ category }: { category: Category | string | null }) {
  if (!category) return <Badge>—</Badge>;
  return <Badge tone={tones[category] || "neutral"}>{labels[category] || category}</Badge>;
}
