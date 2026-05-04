from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class TicketEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticket_id: str
    event_type: str
    payload: dict[str, Any] | None
    actor: str | None
    created_at: datetime
