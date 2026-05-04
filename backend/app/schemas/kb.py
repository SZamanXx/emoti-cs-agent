from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class KbUploadIn(BaseModel):
    title: str
    source_type: str = "md"  # md|pdf|docx|txt|html
    source_url: str | None = None
    category_tags: list[str] | None = None
    body: str  # raw text
    metadata: dict[str, Any] | None = None


class KbUpdateIn(BaseModel):
    title: str | None = None
    body: str | None = None
    category_tags: list[str] | None = None
    source_url: str | None = None


class KbDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    source_type: str
    source_url: str | None
    category_tags: list[str] | None
    summary: str | None
    char_count: int
    created_at: datetime
    updated_at: datetime


class KbDocumentFull(KbDocumentOut):
    body_raw: str
    chunk_count: int = 0


class KbSearchHit(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    content: str
    relevance: float
    category_tags: list[str] | None
