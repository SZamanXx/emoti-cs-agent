"""Mock CMS adapter — voucher code extraction, lookup, privilege separation."""
from __future__ import annotations

import pytest

from app.adapters.cms.mock import MockCMS, extract_voucher_code, serialize_cms_context


class TestExtractVoucherCode:
    def test_basic_wprz(self):
        assert extract_voucher_code("Voucher WPRZ-184220 nie działa") == "WPRZ-184220"

    def test_with_spaces(self):
        # T-003: "WPRZ 244 818"
        code = extract_voucher_code("kod wpisałam już 5 razy WPRZ 244 818")
        assert code == "WPRZ-244818"

    def test_corp(self):
        code = extract_voucher_code("Zgubiłem voucher korporacyjny CORP-ABC-200111")
        assert code == "CORP-ABC-200111"

    def test_gc(self):
        assert extract_voucher_code("Mój kod to GC-12345678") == "GC-12345678"

    def test_no_code(self):
        assert extract_voucher_code("Voucher nie działa wcale") is None

    def test_empty(self):
        assert extract_voucher_code(None) is None
        assert extract_voucher_code("") is None


@pytest.mark.asyncio
class TestMockCMSFetch:
    async def test_known_active_voucher(self):
        cms = MockCMS()
        ctx = await cms.fetch_context(voucher_code="WPRZ-184220", customer_email=None, channel_thread_id=None)
        assert ctx.voucher_code == "WPRZ-184220"
        assert ctx.voucher_status == "active"
        assert ctx.voucher_amount_pln == 449.0

    async def test_expired_voucher(self):
        cms = MockCMS()
        ctx = await cms.fetch_context(voucher_code="WPRZ-401223", customer_email=None, channel_thread_id=None)
        assert ctx.voucher_status == "expired"

    async def test_redeemed_voucher(self):
        cms = MockCMS()
        ctx = await cms.fetch_context(voucher_code="WPRZ-660014", customer_email=None, channel_thread_id=None)
        assert ctx.voucher_status == "redeemed"
        assert ctx.redeemed_at is not None

    async def test_unknown_voucher_returns_empty_context(self):
        cms = MockCMS()
        ctx = await cms.fetch_context(voucher_code="WPRZ-999999", customer_email=None, channel_thread_id=None)
        assert ctx.voucher_status is None

    async def test_normalizes_lowercase_input(self):
        cms = MockCMS()
        ctx = await cms.fetch_context(voucher_code="wprz-184220", customer_email=None, channel_thread_id=None)
        assert ctx.voucher_status == "active"


@pytest.mark.asyncio
class TestPrivilegeSeparation:
    async def test_refund_requires_approver(self):
        cms = MockCMS()
        result = await cms.request_refund(
            voucher_code="WPRZ-300120", amount_pln=400.0, reason="14-day refund window", approver=""
        )
        assert result["ok"] is False
        assert "approver" in result["error"].lower()

    async def test_refund_with_approver_succeeds(self):
        cms = MockCMS()
        result = await cms.request_refund(
            voucher_code="WPRZ-300120", amount_pln=400.0, reason="14-day refund window", approver="supervisor.a"
        )
        assert result["ok"] is True
        assert result["approver"] == "supervisor.a"


class TestSerializeCmsContext:
    def test_includes_status_and_amount(self):
        from app.adapters.cms.protocol import CmsContext
        ctx = CmsContext(
            voucher_code="WPRZ-184220",
            voucher_status="active",
            voucher_amount_pln=449.0,
            purchased_at="2024-08-12",
        )
        s = serialize_cms_context(ctx)
        assert "WPRZ-184220" in s
        assert "active" in s
        assert "449" in s
        assert "2024-08-12" in s

    def test_empty_when_nothing_known(self):
        from app.adapters.cms.protocol import CmsContext
        ctx = CmsContext()
        assert serialize_cms_context(ctx) == ""
