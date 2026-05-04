"""Orchestrator: ticket -> pre-filter -> classifier (+judge in parallel) -> routing -> drafter.

Every major step records a TicketEvent and commits it immediately, so the frontend can
poll `GET /api/v1/tickets/{id}/events` and render a live progress timeline while the
pipeline runs.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.cms.mock import MockCMS, extract_voucher_code, serialize_cms_context
from app.adapters.cms.protocol import CmsAdapter
from app.config import get_settings
from app.models.ticket import Draft, Ticket, TicketEvent
from app.services import drafter as drafter_service
from app.services import killswitch as killswitch_service
from app.services import retriever as retriever_service
from app.services.audit import write_audit
from app.services.classifier import classify
from app.services.defense import run_pre_filter
from app.services.judge import judge_injection

logger = logging.getLogger(__name__)
_settings = get_settings()
_cms: CmsAdapter = MockCMS()


@dataclass
class PipelineOutcome:
    status: str  # drafted | escalated_human | rejected_killswitch
    ticket_id: str
    draft: Draft | None = None
    escalation_reason: str | None = None


async def _record_event(
    session: AsyncSession,
    ticket_id: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
) -> None:
    """Append-and-commit a ticket event so live polling sees the progress as it happens."""
    session.add(TicketEvent(ticket_id=ticket_id, event_type=event_type, payload=payload))
    await session.commit()


async def _set_status(session: AsyncSession, ticket: Ticket, status: str) -> None:
    ticket.status = status
    ticket.updated_at = datetime.now(timezone.utc)
    await session.commit()


def _ms_since(t0: float) -> int:
    return int((time.monotonic() - t0) * 1000)


async def run_pipeline(session: AsyncSession, ticket: Ticket) -> PipelineOutcome:
    t0 = time.monotonic()
    await _record_event(session, ticket.id, "pipeline_started", {"source": ticket.source})

    # Layer 2: pattern pre-filter
    pre_t0 = time.monotonic()
    pre = run_pre_filter(f"{ticket.subject or ''}\n\n{ticket.body}")
    if pre.suspected:
        ticket.suspected_injection = True
        ticket.injection_signals = {"pre_filter": pre.signals}
    await _record_event(
        session,
        ticket.id,
        "pre_filter_done",
        {"suspected": pre.suspected, "signals": pre.signals, "elapsed_ms": _ms_since(pre_t0)},
    )

    # Layer 3 + classification, in parallel for latency
    await _record_event(
        session, ticket.id, "classify_started", {"models": ["haiku-classifier", "haiku-judge"]}
    )
    cls_t0 = time.monotonic()
    classify_task = asyncio.create_task(classify(ticket_subject=ticket.subject, ticket_body=ticket.body))
    judge_task = asyncio.create_task(judge_injection(ticket.body))
    classification, judgment = await asyncio.gather(classify_task, judge_task)

    ticket.category = classification.category
    ticket.classifier_confidence = classification.confidence
    ticket.classifier_reasoning = classification.reasoning

    combined_injection = (
        pre.suspected or classification.suspected_injection or judgment.is_injection
    )
    if combined_injection:
        ticket.suspected_injection = True
        sig: dict[str, Any] = ticket.injection_signals or {}
        sig["classifier"] = classification.injection_signals
        sig["judge"] = {
            "is_injection": judgment.is_injection,
            "signals": judgment.signals,
            "confidence": judgment.confidence,
        }
        ticket.injection_signals = sig

    await write_audit(
        session,
        action="classify",
        ticket_id=ticket.id,
        prompt_version="classifier:v1.0.0;judge:v1.0.0",
        usage=classification.raw.usage,
        payload={
            "category": classification.category,
            "confidence": classification.confidence,
            "judge_is_injection": judgment.is_injection,
            "pre_filter_signals": pre.signals,
        },
    )
    await write_audit(
        session,
        action="judge",
        ticket_id=ticket.id,
        prompt_version="judge:v1.0.0",
        usage=judgment.raw.usage,
    )
    await _record_event(
        session,
        ticket.id,
        "classify_done",
        {
            "category": classification.category,
            "confidence": classification.confidence,
            "suspected_injection": bool(combined_injection),
            "judge_is_injection": judgment.is_injection,
            "classifier_cost_usd": classification.raw.usage.cost_usd,
            "judge_cost_usd": judgment.raw.usage.cost_usd,
            "elapsed_ms": _ms_since(cls_t0),
        },
    )
    await _set_status(session, ticket, "classified")

    # Killswitch checks
    global_on = await killswitch_service.is_enabled(session, "global")
    drafter_on = await killswitch_service.is_enabled(session, "feature:drafter")
    category_on = await killswitch_service.is_enabled(session, killswitch_service.category_scope(classification.category))

    if not (global_on and drafter_on and category_on):
        await _record_event(
            session,
            ticket.id,
            "killswitch_blocked",
            {"global": global_on, "drafter": drafter_on, "category": category_on},
        )
        await _set_status(session, ticket, "escalated_human")
        await _record_event(
            session,
            ticket.id,
            "pipeline_completed",
            {"status": "escalated_human", "reason": "killswitch", "total_ms": _ms_since(t0)},
        )
        return PipelineOutcome(
            status="escalated_human",
            ticket_id=ticket.id,
            escalation_reason="killswitch active",
        )

    # Refund + supplier_dispute -> escalate without drafting (refund pushback)
    if classification.category in _settings.escalation_categories:
        await _record_event(
            session,
            ticket.id,
            "auto_escalated",
            {"category": classification.category, "policy": "refund_pushback_no_draft"},
        )
        await _set_status(session, ticket, "escalated_human")
        await _record_event(
            session,
            ticket.id,
            "pipeline_completed",
            {
                "status": "escalated_human",
                "reason": f"category={classification.category}",
                "total_ms": _ms_since(t0),
            },
        )
        return PipelineOutcome(
            status="escalated_human",
            ticket_id=ticket.id,
            escalation_reason=f"category={classification.category} routed to human (refund pushback policy)",
        )

    # Injection escalate
    if combined_injection:
        await _record_event(
            session, ticket.id, "auto_escalated", {"reason": "injection_suspected"}
        )
        await _set_status(session, ticket, "escalated_human")
        await _record_event(
            session,
            ticket.id,
            "pipeline_completed",
            {
                "status": "escalated_human",
                "reason": "suspected prompt injection",
                "total_ms": _ms_since(t0),
            },
        )
        return PipelineOutcome(
            status="escalated_human",
            ticket_id=ticket.id,
            escalation_reason="suspected prompt injection",
        )

    # KB retrieval + CMS context
    kb_t0 = time.monotonic()
    voucher = extract_voucher_code(
        f"{ticket.subject or ''} {ticket.body} "
        f"{(ticket.extra_metadata or {}).get('voucher_code_guess', '')}"
    )
    cms_ctx = await _cms.fetch_context(
        voucher_code=voucher,
        customer_email=ticket.from_email,
        channel_thread_id=ticket.channel_thread_id,
    )
    cms_text = serialize_cms_context(cms_ctx)

    retrieved = await retriever_service.retrieve(
        session,
        query=f"{classification.category} {ticket.subject or ''} {ticket.body}",
        category=classification.category,
    )
    await _record_event(
        session,
        ticket.id,
        "kb_retrieval_done",
        {
            "voucher_code": voucher,
            "voucher_status": cms_ctx.voucher_status,
            "chunks_retrieved": len(retrieved),
            "top_doc": retrieved[0].document_title if retrieved else None,
            "elapsed_ms": _ms_since(kb_t0),
        },
    )

    # Drafter
    await _record_event(
        session,
        ticket.id,
        "drafter_started",
        {"model": _settings.anthropic_model_drafter, "category": classification.category},
    )
    draft_t0 = time.monotonic()
    payload = await drafter_service.generate_draft(
        ticket_subject=ticket.subject,
        ticket_body=ticket.body,
        category=classification.category,
        retrieved=retrieved,
        cms_context=cms_text or None,
    )

    draft = Draft(
        ticket_id=ticket.id,
        version=1,
        subject=payload.subject,
        body_text=payload.body_text,
        body_html=payload.body_html,
        recipient=payload.recipient or ticket.from_email,
        confidence=payload.confidence,
        requires_action=payload.requires_action,
        action_type=payload.action_type,
        action_params=payload.action_params,
        citations=payload.citations,
        warnings=payload.warnings,
        prompt_version=drafter_service.get_prompt_version(),
        model_name=payload.raw.usage.model,
        input_tokens=payload.raw.usage.input_tokens,
        cached_input_tokens=payload.raw.usage.cached_input_tokens,
        output_tokens=payload.raw.usage.output_tokens,
        cost_usd=payload.raw.usage.cost_usd,
        status="draft",
    )
    session.add(draft)
    await session.flush()

    await write_audit(
        session,
        action="draft",
        ticket_id=ticket.id,
        draft_id=draft.id,
        prompt_version=drafter_service.get_prompt_version(),
        usage=payload.raw.usage,
        payload={
            "category": classification.category,
            "requires_action": payload.requires_action,
            "warnings": payload.warnings,
            "citation_count": len(payload.citations),
        },
    )

    await _record_event(
        session,
        ticket.id,
        "drafted",
        {
            "draft_id": draft.id,
            "confidence": payload.confidence,
            "requires_action": payload.requires_action,
            "action_type": payload.action_type,
            "warnings_count": len(payload.warnings),
            "citations_count": len(payload.citations),
            "input_tokens": payload.raw.usage.input_tokens,
            "cached_input_tokens": payload.raw.usage.cached_input_tokens,
            "output_tokens": payload.raw.usage.output_tokens,
            "cost_usd": payload.raw.usage.cost_usd,
            "elapsed_ms": _ms_since(draft_t0),
        },
    )

    if payload.requires_action:
        await _set_status(session, ticket, "in_review")
    else:
        await _set_status(session, ticket, "drafted")

    await _record_event(
        session,
        ticket.id,
        "pipeline_completed",
        {
            "status": ticket.status,
            "draft_id": draft.id,
            "total_ms": _ms_since(t0),
        },
    )

    return PipelineOutcome(status="drafted", ticket_id=ticket.id, draft=draft)


async def get_latest_draft(session: AsyncSession, ticket_id: str) -> Draft | None:
    stmt = (
        select(Draft).where(Draft.ticket_id == ticket_id).order_by(Draft.version.desc(), Draft.created_at.desc()).limit(1)
    )
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def list_ticket_events(session: AsyncSession, ticket_id: str) -> list[TicketEvent]:
    stmt = (
        select(TicketEvent)
        .where(TicketEvent.ticket_id == ticket_id)
        .order_by(TicketEvent.created_at.asc(), TicketEvent.id.asc())
    )
    res = await session.execute(stmt)
    return list(res.scalars().all())
