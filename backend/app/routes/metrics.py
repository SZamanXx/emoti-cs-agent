from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.models.audit import AuditLog
from app.models.ticket import Draft, Ticket
from app.security.api_key import require_api_key

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])
_settings = get_settings()


@router.get("")
async def get_metrics(
    api_key: str = Depends(require_api_key),
    session: AsyncSession = Depends(get_session),
    days: int = Query(default=7, ge=1, le=90),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)

    stmt = select(
        func.count(Ticket.id).label("tickets"),
        Ticket.category,
    ).where(Ticket.tenant_id == _settings.tenant_id, Ticket.created_at >= since).group_by(Ticket.category)
    rows = (await session.execute(stmt)).all()
    by_category = {(r.category or "unclassified"): int(r.tickets) for r in rows}

    cost_stmt = select(
        func.coalesce(func.sum(AuditLog.cost_usd), 0.0).label("total_cost"),
        func.coalesce(func.sum(AuditLog.input_tokens), 0).label("input_tokens"),
        func.coalesce(func.sum(AuditLog.cached_input_tokens), 0).label("cached_input_tokens"),
        func.coalesce(func.sum(AuditLog.cache_creation_tokens), 0).label("cache_creation_tokens"),
        func.coalesce(func.sum(AuditLog.output_tokens), 0).label("output_tokens"),
    ).where(AuditLog.tenant_id == _settings.tenant_id, AuditLog.created_at >= since)
    cost_row = (await session.execute(cost_stmt)).one()

    cache_total = (cost_row.cached_input_tokens or 0) + (cost_row.cache_creation_tokens or 0)
    cache_hit_rate = (cost_row.cached_input_tokens or 0) / cache_total if cache_total else 0.0

    accept_stmt = select(
        func.count(Draft.id).filter(Draft.status == "accepted").label("accepted"),
        func.count(Draft.id).filter(Draft.status == "edited").label("edited"),
        func.count(Draft.id).filter(Draft.status == "rejected").label("rejected"),
        func.count(Draft.id).label("total"),
    )
    accept = (await session.execute(accept_stmt)).one()
    accept_rate = (accept.accepted or 0) / (accept.total or 1) if accept.total else 0.0

    cost_per_ticket = float(cost_row.total_cost or 0.0) / (sum(by_category.values()) or 1)

    return {
        "window_days": days,
        "tickets_total": sum(by_category.values()),
        "tickets_by_category": by_category,
        "cost_usd_total": float(cost_row.total_cost or 0.0),
        "cost_usd_per_ticket": cost_per_ticket,
        "cost_pln_total_estimate": float(cost_row.total_cost or 0.0) * 3.62,
        "cache_hit_rate": cache_hit_rate,
        "tokens": {
            "input": int(cost_row.input_tokens or 0),
            "cached_input": int(cost_row.cached_input_tokens or 0),
            "cache_creation": int(cost_row.cache_creation_tokens or 0),
            "output": int(cost_row.output_tokens or 0),
        },
        "drafts": {
            "total": int(accept.total or 0),
            "accepted": int(accept.accepted or 0),
            "edited": int(accept.edited or 0),
            "rejected": int(accept.rejected or 0),
            "accept_without_edit_rate": accept_rate,
        },
    }
