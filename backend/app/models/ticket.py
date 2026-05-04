from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid() -> str:
    return f"tkt_{uuid4().hex[:24]}"


def _draft_uuid() -> str:
    return f"drf_{uuid4().hex[:24]}"


def _event_uuid() -> str:
    return f"evt_{uuid4().hex[:24]}"


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String, nullable=False)  # email|chat|form|manual|cms
    channel_thread_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    from_email: Mapped[str | None] = mapped_column(String, nullable=True)
    from_phone: Mapped[str | None] = mapped_column(String, nullable=True)
    from_name: Mapped[str | None] = mapped_column(String, nullable=True)
    subject: Mapped[str | None] = mapped_column(String, nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    language_hint: Mapped[str] = mapped_column(String, default="pl", nullable=False)

    category: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    classifier_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    classifier_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    suspected_injection: Mapped[bool] = mapped_column(default=False, nullable=False)
    injection_signals: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[str] = mapped_column(String, default="received", nullable=False, index=True)
    # received | classified | drafted | in_review | approved | edited | rejected | sent | closed | escalated_human

    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    drafts: Mapped[list[Draft]] = relationship(back_populates="ticket", cascade="all, delete-orphan")
    events: Mapped[list[TicketEvent]] = relationship(back_populates="ticket", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_tickets_tenant_status", "tenant_id", "status"),
        Index("ix_tickets_tenant_category", "tenant_id", "category"),
    )


class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_draft_uuid)
    ticket_id: Mapped[str] = mapped_column(String, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(default=1, nullable=False)

    subject: Mapped[str | None] = mapped_column(String, nullable=True)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    recipient: Mapped[str | None] = mapped_column(String, nullable=True)

    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    requires_action: Mapped[bool] = mapped_column(default=False, nullable=False)
    action_type: Mapped[str | None] = mapped_column(String, nullable=True)
    action_params: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    citations: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    warnings: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    prompt_version: Mapped[str] = mapped_column(String, nullable=False)
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    input_tokens: Mapped[int] = mapped_column(default=0, nullable=False)
    cached_input_tokens: Mapped[int] = mapped_column(default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    status: Mapped[str] = mapped_column(String, default="draft", nullable=False)  # draft | accepted | edited | rejected | sent
    edited_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ticket: Mapped[Ticket] = relationship(back_populates="drafts")


class TicketEvent(Base):
    __tablename__ = "ticket_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_event_uuid)
    ticket_id: Mapped[str] = mapped_column(String, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    actor: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ticket: Mapped[Ticket] = relationship(back_populates="events")
