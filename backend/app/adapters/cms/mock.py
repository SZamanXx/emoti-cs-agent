from __future__ import annotations

import re
from typing import Any

from app.adapters.cms.protocol import CmsContext


# Wyjątkowy Prezent voucher formats (per KB-009):
#  - WPRZ-NNNNNN (regular experience voucher)
#  - GC-NNNNNNNN (Gift Card after expiry of redeem window)
#  - MUL-, PP-, ALG- (B2B partners)
#  - CORP-AAA-NNNNNN (corporate)
#  - STORE-NNNNNNNNNN (printed in-store)
_VOUCHER_RE = re.compile(
    r"\b(WPRZ|GC|MUL|PP|ALG|CORP|STORE)[-\s]?(?:[A-Z]{1,4}[-\s]?)?\d{1,4}(?:[-\s]?\d{1,4}){0,3}\b",
    re.I,
)


_FAKE_VOUCHERS = {
    # Codes that match sample_data/tickets.jsonl
    "WPRZ-184220": {
        "voucher_status": "active",
        "voucher_amount_pln": 449.0,
        "purchased_at": "2024-08-12",
        "expires_at": "2027-08-12",
        "redeemed_at": None,
        "reservation_id": None,
        "reservation_status": None,
        "reservation_supplier": None,
        "payment_method": "card",
        "refund_eligible": False,  # >101 days since purchase
        "refund_window_remaining_days": 0,
        "experience_name": "Weekend SPA dla dwojga",
        "supplier_id": "sup-77",
    },
    "WPRZ-101991": {
        "voucher_status": "active",
        "voucher_amount_pln": 299.0,
        "purchased_at": "2023-09-15",
        "expires_at": "2026-09-15",
        "redeemed_at": None,
        "payment_method": "blik",
        "refund_eligible": False,
        "refund_window_remaining_days": 0,
        "experience_name": "Lot widokowy szybowcem",
        "supplier_id": "sup-12",
    },
    "WPRZ-244818": {
        "voucher_status": "active",
        "voucher_amount_pln": 199.0,
        "purchased_at": "2025-03-20",
        "expires_at": "2028-03-20",
        "redeemed_at": None,
        "payment_method": "card",
        "refund_eligible": False,
        "refund_window_remaining_days": 0,
        "experience_name": "Masaż relaksacyjny Warszawa",
        "supplier_id": "sup-31",
    },
    "WPRZ-300120": {
        "voucher_status": "active",
        "voucher_amount_pln": 400.0,
        "purchased_at": "2026-04-19",
        "expires_at": "2029-04-19",
        "redeemed_at": None,
        "payment_method": "card",
        "refund_eligible": True,  # within 101 days, refund possible
        "refund_window_remaining_days": 86,
        "experience_name": "Voucher uniwersalny 400 PLN",
        "supplier_id": "sup-99",
    },
    "WPRZ-510221": {
        "voucher_status": "active",
        "voucher_amount_pln": 320.0,
        "purchased_at": "2025-08-15",
        "expires_at": "2028-08-15",
        "redeemed_at": None,
        "payment_method": "card",
        "refund_eligible": False,
        "refund_window_remaining_days": 0,
        "experience_name": "Masaż dla dwojga Warszawa",
        "supplier_id": "sup-31",
    },
    "WPRZ-660014": {
        "voucher_status": "redeemed",
        "voucher_amount_pln": 350.0,
        "purchased_at": "2025-11-02",
        "expires_at": "2028-11-02",
        "redeemed_at": "2026-04-28",
        "reservation_id": "RES-9912",
        "reservation_status": "completed",
        "reservation_supplier": "Whisky Bar Kraków",
        "payment_method": "card",
        "refund_eligible": False,
        "refund_window_remaining_days": 0,
        "experience_name": "Degustacja whisky Kraków",
        "supplier_id": "sup-44",
    },
    "WPRZ-714221": {
        "voucher_status": "redeemed",
        "voucher_amount_pln": 280.0,
        "purchased_at": "2025-10-12",
        "expires_at": "2028-10-12",
        "redeemed_at": "2026-04-04",
        "reservation_id": "RES-7700",
        "reservation_status": "disputed",
        "reservation_supplier": "Salon masażu Gdańsk",
        "payment_method": "blik",
        "refund_eligible": True,
        "refund_window_remaining_days": 0,
        "experience_name": "Masaż 60 min Gdańsk",
        "supplier_id": "sup-58",
    },
    "WPRZ-401223": {
        "voucher_status": "expired",
        "voucher_amount_pln": 250.0,
        "purchased_at": "2023-04-01",
        "expires_at": "2026-04-01",
        "redeemed_at": None,
        "payment_method": "card",
        "refund_eligible": False,
        "refund_window_remaining_days": 0,
        "experience_name": "Karnet dla dwojga",
        "supplier_id": "sup-19",
    },
    "CORP-ABC-200111": {
        "voucher_status": "active",
        "voucher_amount_pln": 600.0,
        "purchased_at": "2025-09-10",
        "expires_at": "2027-09-10",
        "redeemed_at": None,
        "payment_method": "invoice",
        "refund_eligible": False,
        "refund_window_remaining_days": 0,
        "experience_name": "Voucher korporacyjny 600 PLN (firma X)",
        "supplier_id": None,
    },
}


class MockCMS:
    async def fetch_context(
        self,
        *,
        voucher_code: str | None,
        customer_email: str | None,
        channel_thread_id: str | None,
    ) -> CmsContext:
        code = (voucher_code or "").strip().upper().replace(" ", "")
        rec = _FAKE_VOUCHERS.get(code)
        if rec:
            field_keys = {f.name for f in CmsContext.__dataclass_fields__.values() if f.name != "raw"}
            init_kwargs = {k: v for k, v in rec.items() if k in field_keys}
            return CmsContext(voucher_code=code, raw=dict(rec), **init_kwargs)
        return CmsContext(voucher_code=code or None)

    async def request_refund(
        self, *, voucher_code: str, amount_pln: float, reason: str, approver: str
    ) -> dict[str, Any]:
        # Privilege-separated: gated on `approver` (a human supervisor identifier).
        if not approver:
            return {"ok": False, "error": "approver required"}
        return {
            "ok": True,
            "voucher_code": voucher_code,
            "amount_pln": amount_pln,
            "reason": reason,
            "approver": approver,
            "request_id": "rf_mock_demo_only",
        }

    async def mark_supplier_dispute(
        self, *, voucher_code: str, supplier: str, notes: str, approver: str
    ) -> dict[str, Any]:
        return {
            "ok": True,
            "case_id": "case_mock_demo_only",
            "voucher_code": voucher_code,
            "supplier": supplier,
            "notes": notes,
            "approver": approver,
        }


def extract_voucher_code(text: str | None) -> str | None:
    if not text:
        return None
    m = _VOUCHER_RE.search(text)
    if not m:
        return None
    raw = m.group(0).replace(" ", "").upper()
    # Normalize: insert hyphen between prefix-letters and digits if missing.
    norm = re.sub(r"^(WPRZ|GC|MUL|PP|ALG|STORE)(\d)", r"\1-\2", raw)
    norm = re.sub(r"^(CORP)([A-Z]{1,4})(\d)", r"\1-\2-\3", norm)
    return norm


def serialize_cms_context(ctx: CmsContext) -> str:
    if ctx.voucher_status is None and not ctx.voucher_code:
        return ""
    lines = [
        f"voucher_code: {ctx.voucher_code or 'unknown'}",
        f"voucher_status: {ctx.voucher_status or 'unknown'}",
    ]
    if ctx.voucher_amount_pln is not None:
        lines.append(f"voucher_amount_pln: {ctx.voucher_amount_pln}")
    if ctx.purchased_at:
        lines.append(f"purchased_at: {ctx.purchased_at}")
    if ctx.expires_at:
        lines.append(f"expires_at: {ctx.expires_at}")
    if ctx.redeemed_at:
        lines.append(f"redeemed_at: {ctx.redeemed_at}")
    if ctx.reservation_id:
        lines.append(f"reservation: {ctx.reservation_id} status={ctx.reservation_status} supplier={ctx.reservation_supplier}")
    if ctx.payment_method:
        lines.append(f"payment_method: {ctx.payment_method}")
    if ctx.refund_eligible is not None:
        lines.append(f"refund_eligible: {ctx.refund_eligible}")
    if ctx.refund_window_remaining_days is not None:
        lines.append(f"refund_window_remaining_days: {ctx.refund_window_remaining_days}")
    extra = ctx.raw or {}
    if extra.get("experience_name"):
        lines.append(f"experience: {extra['experience_name']}")
    if extra.get("supplier_id"):
        lines.append(f"supplier_id: {extra['supplier_id']}")
    return "\n".join(lines)
