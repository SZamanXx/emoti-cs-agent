from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.security.api_key import require_api_key
from app.services import killswitch as killswitch_service

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class KillswitchOut(BaseModel):
    scope: str
    enabled: bool
    auto_disabled: bool
    reason: str | None
    last_changed_by: str | None


class KillswitchUpdate(BaseModel):
    enabled: bool
    reason: str | None = None
    actor: str | None = None


@router.get("/killswitches", response_model=list[KillswitchOut])
async def list_kill(
    api_key: str = Depends(require_api_key),
    session: AsyncSession = Depends(get_session),
):
    rows = await killswitch_service.list_killswitches(session)
    return [
        KillswitchOut(
            scope=r.scope,
            enabled=r.enabled,
            auto_disabled=r.auto_disabled,
            reason=r.reason,
            last_changed_by=r.last_changed_by,
        )
        for r in rows
    ]


@router.put("/killswitches/{scope:path}", response_model=KillswitchOut)
async def update_kill(
    scope: str,
    payload: KillswitchUpdate,
    api_key: str = Depends(require_api_key),
    session: AsyncSession = Depends(get_session),
):
    row = await killswitch_service.set_enabled(
        session, scope, enabled=payload.enabled, reason=payload.reason, actor=payload.actor or api_key
    )
    await session.commit()
    return KillswitchOut(
        scope=row.scope,
        enabled=row.enabled,
        auto_disabled=row.auto_disabled,
        reason=row.reason,
        last_changed_by=row.last_changed_by,
    )
