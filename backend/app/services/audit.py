from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.llm.anthropic_client import LLMUsage
from app.models.audit import AuditLog

_settings = get_settings()


async def write_audit(
    session: AsyncSession,
    *,
    action: str,
    ticket_id: str | None = None,
    draft_id: str | None = None,
    actor: str | None = None,
    prompt_version: str | None = None,
    usage: LLMUsage | None = None,
    payload: dict[str, Any] | None = None,
    notes: str | None = None,
) -> AuditLog:
    row = AuditLog(
        tenant_id=_settings.tenant_id,
        ticket_id=ticket_id,
        draft_id=draft_id,
        action=action,
        actor=actor,
        prompt_version=prompt_version,
        model_name=usage.model if usage else None,
        input_tokens=usage.input_tokens if usage else 0,
        cached_input_tokens=usage.cached_input_tokens if usage else 0,
        cache_creation_tokens=usage.cache_creation_tokens if usage else 0,
        output_tokens=usage.output_tokens if usage else 0,
        cost_usd=usage.cost_usd if usage else 0.0,
        payload=payload,
        notes=notes,
    )
    session.add(row)
    await session.flush()
    return row
