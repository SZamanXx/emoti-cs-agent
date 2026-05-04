from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class Citation(BaseModel):
    chunk_id: str
    document_title: str
    snippet: str
    relevance: float | None = None


class DraftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticket_id: str
    version: int

    subject: str | None
    body_text: str
    body_html: str | None
    recipient: str | None

    confidence: float
    requires_action: bool
    action_type: str | None
    action_params: dict[str, Any] | None

    citations: list[dict[str, Any]] | None
    warnings: list[str] | None

    prompt_version: str
    model_name: str
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    cost_usd: float

    status: str
    edited_body: str | None
    reviewed_by: str | None
    reviewed_at: datetime | None
    created_at: datetime


class DraftResponse(BaseModel):
    ticket_id: str
    status: str
    draft: DraftOut | None = None
    escalation_reason: str | None = None


class ReviewAction(BaseModel):
    action: str  # accept | edit | reject
    edited_body: str | None = None
    reason: str | None = None
    reviewed_by: str | None = None


class SendRequest(BaseModel):
    approved_by: str | None = None
    edits: str | None = None
    send_via: str | None = None  # channel_thread_id override
