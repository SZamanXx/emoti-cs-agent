from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class CmsContext:
    voucher_code: str | None = None
    voucher_status: str | None = None  # active|redeemed|expired|cancelled|unknown
    voucher_amount_pln: float | None = None
    purchased_at: str | None = None
    expires_at: str | None = None
    redeemed_at: str | None = None

    reservation_id: str | None = None
    reservation_status: str | None = None
    reservation_supplier: str | None = None

    payment_method: str | None = None
    refund_eligible: bool | None = None
    refund_window_remaining_days: int | None = None

    raw: dict[str, Any] = field(default_factory=dict)


class CmsAdapter(Protocol):
    """Minimum surface the system expects from a CMS connector.

    Pushback artifact: this protocol is what we'd ask the Emoti CMS team to expose, ideally as one
    composite endpoint per ticket so we don't pay 3 sequential round-trips.
    """

    async def fetch_context(self, *, voucher_code: str | None, customer_email: str | None, channel_thread_id: str | None) -> CmsContext: ...

    async def request_refund(self, *, voucher_code: str, amount_pln: float, reason: str, approver: str) -> dict[str, Any]:
        """Privilege-separated. The model never has the credentials to call this directly."""

    async def mark_supplier_dispute(self, *, voucher_code: str, supplier: str, notes: str, approver: str) -> dict[str, Any]: ...
