from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.killswitch import Killswitch

_settings = get_settings()


async def is_enabled(session: AsyncSession, scope: str) -> bool:
    stmt = select(Killswitch).where(
        Killswitch.tenant_id == _settings.tenant_id, Killswitch.scope == scope
    )
    res = await session.execute(stmt)
    row = res.scalar_one_or_none()
    if row is None:
        return True  # default-on
    return row.enabled


async def set_enabled(
    session: AsyncSession, scope: str, *, enabled: bool, reason: str | None = None, actor: str | None = None
) -> Killswitch:
    stmt = (
        pg_insert(Killswitch)
        .values(tenant_id=_settings.tenant_id, scope=scope, enabled=enabled, reason=reason, last_changed_by=actor)
        .on_conflict_do_update(
            index_elements=["tenant_id", "scope"],
            set_={"enabled": enabled, "reason": reason, "last_changed_by": actor},
        )
        .returning(Killswitch)
    )
    res = await session.execute(stmt)
    await session.flush()
    return res.scalar_one()


async def list_killswitches(session: AsyncSession) -> list[Killswitch]:
    stmt = select(Killswitch).where(Killswitch.tenant_id == _settings.tenant_id).order_by(Killswitch.scope)
    res = await session.execute(stmt)
    return list(res.scalars().all())


def category_scope(category: str) -> str:
    return f"category:{category}"


def feature_scope(name: str) -> str:
    return f"feature:{name}"
