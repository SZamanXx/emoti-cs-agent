from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _ks_uuid() -> str:
    return f"ks_{uuid4().hex[:24]}"


class Killswitch(Base):
    __tablename__ = "killswitches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_ks_uuid)
    tenant_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String, nullable=False)  # global | category:<name> | feature:<name>
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_disabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_changed_by: Mapped[str | None] = mapped_column(String, nullable=True)
    last_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("tenant_id", "scope", name="uq_killswitch_tenant_scope"),)
