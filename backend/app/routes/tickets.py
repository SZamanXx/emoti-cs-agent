from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import SessionLocal, get_session
from app.models.ticket import Draft, Ticket
from app.schemas.draft import DraftOut, DraftResponse, ReviewAction, SendRequest
from app.schemas.event import TicketEventOut
from app.schemas.ticket import TicketCreate, TicketOut, TicketSummary
from app.security.api_key import require_api_key
from app.security.hmac_signing import require_hmac
from app.security.idempotency import reserve_idempotency_key
from app.services.audit import write_audit
from app.services.outbound import push_draft_ready
from app.services.pipeline import get_latest_draft, list_ticket_events, run_pipeline

router = APIRouter(prefix="/api/v1/tickets", tags=["tickets"])
_settings = get_settings()


def _payload_hash(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


async def _process_ticket_async(ticket_id: str) -> None:
    """Run pipeline in a fresh DB session (background task)."""
    async with SessionLocal() as session:
        try:
            stmt = select(Ticket).where(Ticket.id == ticket_id)
            t = (await session.execute(stmt)).scalar_one()
            outcome = await run_pipeline(session, t)
            await session.commit()
            payload = {
                "ticket_id": ticket_id,
                "status": outcome.status,
                "draft_id": outcome.draft.id if outcome.draft else None,
                "escalation_reason": outcome.escalation_reason,
            }
            try:
                await push_draft_ready(payload)
            except Exception:  # noqa: BLE001
                pass
        except Exception:  # noqa: BLE001
            await session.rollback()
            raise


@router.post("", response_model=DraftResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_ticket(
    request: Request,
    background: BackgroundTasks,
    body_bytes: bytes = Depends(require_hmac),
    api_key: str = Depends(require_api_key),
    session: AsyncSession = Depends(get_session),
):
    try:
        data = json.loads(body_bytes.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"invalid JSON: {exc}") from exc

    try:
        payload = TicketCreate.model_validate(data)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    idem_key = request.headers.get("X-Idempotency-Key", "")
    payload_hash = _payload_hash(body_bytes)
    accepted, existing = await reserve_idempotency_key(idem_key, payload_hash)
    if not accepted:
        if existing == payload_hash:
            return DraftResponse(ticket_id="duplicate", status="duplicate_idempotent")
        raise HTTPException(status_code=409, detail="idempotency key collision with different payload")

    sender = payload.sender
    ticket = Ticket(
        tenant_id=_settings.tenant_id,
        source=payload.source,
        channel_thread_id=payload.channel_thread_id,
        from_email=sender.email if sender else None,
        from_phone=sender.phone if sender else None,
        from_name=sender.name if sender else None,
        subject=payload.subject,
        body=payload.body,
        language_hint=payload.language_hint,
        received_at=payload.received_at or datetime.now(timezone.utc),
        extra_metadata=payload.metadata,
        status="received",
    )
    session.add(ticket)
    await session.flush()
    await write_audit(session, action="ticket_received", ticket_id=ticket.id, actor=api_key)
    await session.commit()

    background.add_task(_process_ticket_async, ticket.id)

    return DraftResponse(ticket_id=ticket.id, status="queued")


@router.get("", response_model=list[TicketSummary])
async def list_tickets(
    api_key: str = Depends(require_api_key),
    session: AsyncSession = Depends(get_session),
    status_filter: str | None = Query(default=None, alias="status"),
    category: str | None = None,
    limit: int = 100,
):
    stmt = select(Ticket).where(Ticket.tenant_id == _settings.tenant_id)
    if status_filter:
        stmt = stmt.where(Ticket.status == status_filter)
    if category:
        stmt = stmt.where(Ticket.category == category)
    stmt = stmt.order_by(Ticket.created_at.desc()).limit(limit)
    res = await session.execute(stmt)
    rows = list(res.scalars().all())
    return rows


@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(
    ticket_id: str,
    api_key: str = Depends(require_api_key),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Ticket).where(Ticket.id == ticket_id, Ticket.tenant_id == _settings.tenant_id)
    res = await session.execute(stmt)
    t = res.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="ticket not found")
    return t


@router.get("/{ticket_id}/draft", response_model=DraftOut | None)
async def get_draft(
    ticket_id: str,
    api_key: str = Depends(require_api_key),
    session: AsyncSession = Depends(get_session),
):
    draft = await get_latest_draft(session, ticket_id)
    return draft


@router.get("/{ticket_id}/events", response_model=list[TicketEventOut])
async def get_events(
    ticket_id: str,
    api_key: str = Depends(require_api_key),
    session: AsyncSession = Depends(get_session),
):
    """Live pipeline timeline. Each event is one major pipeline step (committed
    immediately so the operator console can poll and render progress while the
    pipeline is still running)."""
    return await list_ticket_events(session, ticket_id)


@router.post("/{ticket_id}/review", response_model=DraftOut)
async def review_draft(
    ticket_id: str,
    action: ReviewAction,
    api_key: str = Depends(require_api_key),
    session: AsyncSession = Depends(get_session),
):
    draft = await get_latest_draft(session, ticket_id)
    if not draft:
        raise HTTPException(status_code=404, detail="no draft")
    if action.action == "accept":
        draft.status = "accepted"
    elif action.action == "edit":
        if not action.edited_body:
            raise HTTPException(status_code=422, detail="edited_body required for edit")
        draft.status = "edited"
        draft.edited_body = action.edited_body
    elif action.action == "reject":
        draft.status = "rejected"
    else:
        raise HTTPException(status_code=422, detail="action must be accept|edit|reject")
    draft.reviewed_by = action.reviewed_by or api_key
    draft.reviewed_at = datetime.now(timezone.utc)

    stmt = select(Ticket).where(Ticket.id == ticket_id)
    ticket = (await session.execute(stmt)).scalar_one()
    if action.action == "accept":
        ticket.status = "approved"
    elif action.action == "edit":
        ticket.status = "edited"
    else:
        ticket.status = "rejected"

    await write_audit(
        session,
        action=f"review_{action.action}",
        ticket_id=ticket_id,
        draft_id=draft.id,
        actor=draft.reviewed_by,
        payload={"reason": action.reason},
    )
    await session.commit()
    return draft


@router.post("/{ticket_id}/send", response_model=DraftOut)
async def send_draft(
    ticket_id: str,
    payload: SendRequest,
    api_key: str = Depends(require_api_key),
    session: AsyncSession = Depends(get_session),
):
    from app.adapters.outbound.chat_stub import ChatStubAdapter
    from app.adapters.outbound.email_stub import EmailStubAdapter

    draft = await get_latest_draft(session, ticket_id)
    if not draft or draft.status not in {"accepted", "edited"}:
        raise HTTPException(status_code=409, detail="draft must be accepted or edited before send")

    stmt = select(Ticket).where(Ticket.id == ticket_id)
    ticket = (await session.execute(stmt)).scalar_one()

    body = draft.edited_body if draft.status == "edited" and draft.edited_body else draft.body_text

    if ticket.source == "chat":
        await ChatStubAdapter().send(channel_thread_id=ticket.channel_thread_id or "", body_text=body)
    else:
        await EmailStubAdapter().send(
            recipient=draft.recipient or ticket.from_email or "",
            subject=draft.subject or (ticket.subject or "Re: zapytanie"),
            body_text=body,
            body_html=draft.body_html,
        )

    draft.status = "sent"
    ticket.status = "sent"
    await write_audit(
        session,
        action="send",
        ticket_id=ticket_id,
        draft_id=draft.id,
        actor=payload.approved_by or api_key,
        payload={"send_via": payload.send_via},
    )
    await session.commit()
    return draft
