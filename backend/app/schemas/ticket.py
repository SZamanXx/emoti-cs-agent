from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TicketSenderIn(BaseModel):
    email: EmailStr | None = None
    phone: str | None = None
    name: str | None = None


class TicketCreate(BaseModel):
    source: str = Field(..., examples=["email", "chat", "form", "manual", "cms"])
    channel_thread_id: str | None = None
    sender: TicketSenderIn | None = None
    subject: str | None = None
    body: str
    received_at: datetime | None = None
    language_hint: str = "pl"
    metadata: dict[str, Any] | None = None


class TicketSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source: str
    channel_thread_id: str | None
    from_name: str | None
    from_email: str | None
    subject: str | None
    body: str
    category: str | None
    classifier_confidence: float | None
    suspected_injection: bool
    status: str
    received_at: datetime
    created_at: datetime
    updated_at: datetime


class TicketOut(TicketSummary):
    classifier_reasoning: str | None
    injection_signals: dict[str, Any] | None
    metadata: dict[str, Any] | None = Field(default=None, alias="extra_metadata")
