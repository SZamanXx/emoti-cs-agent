"""Mock inbound channel adapters (email + chat).

In production these would be wired to real provider webhooks (Gmail OAuth push, Intercom
inbound webhook, etc.). For the demo they accept a payload shaped like a real channel
delivery, normalize it into a TicketCreate, and forward to the same pipeline used by
`POST /api/v1/tickets` — same HMAC validation, same idempotency, same pipeline.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.models.ticket import Ticket
from app.routes.tickets import _process_ticket_async  # reuse the async processor
from app.schemas.draft import DraftResponse
from app.security.api_key import require_api_key
from app.security.hmac_signing import require_hmac
from app.security.idempotency import reserve_idempotency_key
from app.services.audit import write_audit

router = APIRouter(prefix="/api/v1/inbound", tags=["inbound"])
_settings = get_settings()


class EmailIn(BaseModel):
    message_id: str
    thread_id: str | None = None
    from_email: EmailStr
    from_name: str | None = None
    to: list[EmailStr] | None = None
    subject: str | None = None
    body_text: str
    body_html: str | None = None
    received_at: datetime | None = None
    headers: dict[str, str] | None = None


class ChatIn(BaseModel):
    conversation_id: str
    message_id: str
    from_user_id: str
    from_name: str | None = None
    from_email: EmailStr | None = None
    text: str
    sent_at: datetime | None = None


def _hash(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


@router.post("/email", response_model=DraftResponse, status_code=202)
async def inbound_email(
    request: Request,
    background: BackgroundTasks,
    body_bytes: bytes = Depends(require_hmac),
    actor: str = Depends(require_api_key),
    session: AsyncSession = Depends(get_session),
):
    try:
        payload = EmailIn.model_validate_json(body_bytes)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    idem_key = request.headers.get("X-Idempotency-Key") or f"email:{payload.message_id}"
    accepted, existing = await reserve_idempotency_key(idem_key, _hash(body_bytes))
    if not accepted:
        return DraftResponse(ticket_id="duplicate", status="duplicate_idempotent")

    ticket = Ticket(
        tenant_id=_settings.tenant_id,
        source="email",
        channel_thread_id=payload.thread_id or payload.message_id,
        from_email=str(payload.from_email),
        from_name=payload.from_name,
        subject=payload.subject,
        body=payload.body_text,
        language_hint="pl",
        received_at=payload.received_at or datetime.now(timezone.utc),
        extra_metadata={
            "external_id": payload.message_id,
            "headers": payload.headers,
            "body_html_present": bool(payload.body_html),
        },
        status="received",
    )
    session.add(ticket)
    await session.flush()
    await write_audit(session, action="ticket_received", ticket_id=ticket.id, actor=f"inbound:email:{actor}")
    await session.commit()
    background.add_task(_process_ticket_async, ticket.id)
    return DraftResponse(ticket_id=ticket.id, status="queued")


@router.post("/chat", response_model=DraftResponse, status_code=202)
async def inbound_chat(
    request: Request,
    background: BackgroundTasks,
    body_bytes: bytes = Depends(require_hmac),
    actor: str = Depends(require_api_key),
    session: AsyncSession = Depends(get_session),
):
    try:
        payload = ChatIn.model_validate_json(body_bytes)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    idem_key = request.headers.get("X-Idempotency-Key") or f"chat:{payload.message_id}"
    accepted, _ = await reserve_idempotency_key(idem_key, _hash(body_bytes))
    if not accepted:
        return DraftResponse(ticket_id="duplicate", status="duplicate_idempotent")

    ticket = Ticket(
        tenant_id=_settings.tenant_id,
        source="chat",
        channel_thread_id=payload.conversation_id,
        from_email=str(payload.from_email) if payload.from_email else None,
        from_name=payload.from_name,
        from_phone=None,
        subject=None,
        body=payload.text,
        language_hint="pl",
        received_at=payload.sent_at or datetime.now(timezone.utc),
        extra_metadata={
            "external_id": payload.message_id,
            "from_user_id": payload.from_user_id,
            "conversation_id": payload.conversation_id,
        },
        status="received",
    )
    session.add(ticket)
    await session.flush()
    await write_audit(session, action="ticket_received", ticket_id=ticket.id, actor=f"inbound:chat:{actor}")
    await session.commit()
    background.add_task(_process_ticket_async, ticket.id)
    return DraftResponse(ticket_id=ticket.id, status="queued")
