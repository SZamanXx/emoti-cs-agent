"""Eval harness: compares classifier output and pipeline routing decisions vs expected_*.

Maps user-provided expected_category values (which include `suspected_injection` and
`out_of_scope` — not first-class enum values) onto our system:

- expected_category == 'suspected_injection' -> success if ticket.suspected_injection is True
- expected_category == 'out_of_scope'        -> success if status == 'escalated_human' OR category == 'other'
- otherwise                                   -> success if classified category matches

For expected_action we map:
- ai_draft                 -> status in {drafted, in_review, approved, edited, sent}
- ai_draft_then_escalate   -> status drafted/in_review AND draft has requires_action == True (or warnings non-empty)
- escalate_human           -> status == 'escalated_human'
- escalate_human_empathy   -> status == 'escalated_human' (we don't separately model empathy yet — flagged in audit)
- quarantine_escalate      -> status == 'escalated_human' AND ticket.suspected_injection True
"""
from __future__ import annotations

import asyncio
import json

from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.models.audit import AuditLog
from app.models.ticket import Draft, Ticket

_settings = get_settings()


def _category_match(expected: str | None, actual_category: str | None, suspected_injection: bool, status: str) -> bool:
    if expected is None:
        return True
    if expected == "suspected_injection":
        return suspected_injection
    if expected == "out_of_scope":
        return actual_category == "other" or status == "escalated_human"
    if expected == "expired_voucher":
        return actual_category == "expired_complaint"
    return actual_category == expected


def _action_match(expected: str | None, status: str, suspected_injection: bool, draft: Draft | None) -> bool:
    if expected is None:
        return True
    if expected == "ai_draft":
        return status in {"drafted", "in_review", "approved", "edited", "sent"}
    if expected == "ai_draft_then_escalate":
        if status not in {"drafted", "in_review"}:
            return False
        if draft is None:
            return False
        return draft.requires_action or bool(draft.warnings)
    if expected == "escalate_human":
        return status == "escalated_human"
    if expected == "escalate_human_empathy":
        return status == "escalated_human"
    if expected == "quarantine_escalate":
        return status == "escalated_human" and suspected_injection
    return False


async def main() -> dict:
    async with SessionLocal() as session:
        tickets = (
            (await session.execute(select(Ticket).where(Ticket.tenant_id == _settings.tenant_id))).scalars().all()
        )

        results: list[dict] = []
        cat_pass = 0
        action_pass = 0
        evaluated = 0
        for t in tickets:
            meta = t.extra_metadata or {}
            expected_category = meta.get("expected_category")
            expected_action = meta.get("expected_action")
            if expected_category is None and expected_action is None:
                continue
            evaluated += 1

            draft = (
                await session.execute(
                    select(Draft).where(Draft.ticket_id == t.id).order_by(Draft.version.desc(), Draft.created_at.desc()).limit(1)
                )
            ).scalar_one_or_none()

            cat_ok = _category_match(expected_category, t.category, t.suspected_injection, t.status)
            act_ok = _action_match(expected_action, t.status, t.suspected_injection, draft)
            if cat_ok:
                cat_pass += 1
            if act_ok:
                action_pass += 1
            results.append(
                {
                    "ticket_id": t.id,
                    "external_id": meta.get("external_id"),
                    "expected_category": expected_category,
                    "actual_category": t.category,
                    "category_pass": cat_ok,
                    "expected_action": expected_action,
                    "actual_status": t.status,
                    "suspected_injection": t.suspected_injection,
                    "draft_requires_action": draft.requires_action if draft else None,
                    "draft_warnings": draft.warnings if draft else None,
                    "action_pass": act_ok,
                }
            )

        cost_total = (
            (await session.execute(
                select(AuditLog.cost_usd).where(AuditLog.tenant_id == _settings.tenant_id)
            )).scalars().all()
        )
        total_cost = sum(cost_total)

        summary = {
            "evaluated": evaluated,
            "category_accuracy": cat_pass / evaluated if evaluated else 0.0,
            "action_accuracy": action_pass / evaluated if evaluated else 0.0,
            "total_cost_usd": total_cost,
            "total_cost_pln_estimate": total_cost * 3.62,
            "per_ticket": results,
        }

        print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
        return summary


if __name__ == "__main__":
    asyncio.run(main())
