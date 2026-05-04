"""Drafter prompt structure tests + brand voice presence."""
from __future__ import annotations

from app.llm.prompts.drafter import (
    DRAFTER_BRAND_VOICE,
    DRAFTER_PROMPT_VERSION,
    DRAFTER_SYSTEM,
    DRAFTER_TOOL,
    build_drafter_messages,
    drafter_system_blocks,
)


class TestBrandVoice:
    def test_polish_sign_off(self):
        assert "Pozdrawiam serdecznie" in DRAFTER_BRAND_VOICE

    def test_brand_name(self):
        assert "Wyjątkowy Prezent" in DRAFTER_BRAND_VOICE

    def test_no_czesc(self):
        assert '"Cześć"' in DRAFTER_BRAND_VOICE  # explicitly forbidden

    def test_36_month_validity(self):
        assert "36 mies" in DRAFTER_BRAND_VOICE or "36 miesięcy" in DRAFTER_BRAND_VOICE

    def test_101_day_refund(self):
        assert "101 dni" in DRAFTER_BRAND_VOICE

    def test_voucher_format(self):
        assert "WPRZ" in DRAFTER_BRAND_VOICE

    def test_factuality_rule(self):
        assert "sprawdzimy i odpiszemy" in DRAFTER_BRAND_VOICE


class TestDrafterPromptStructure:
    def test_version_present(self):
        assert DRAFTER_PROMPT_VERSION

    def test_two_cached_blocks_when_kb_provided(self):
        blocks = drafter_system_blocks("KB CONTEXT EXAMPLE")
        assert len(blocks) == 2
        for b in blocks:
            assert b["cache_control"] == {"type": "ephemeral"}
        assert "<kb_context>" in blocks[1]["text"]

    def test_one_cached_block_when_no_kb(self):
        blocks = drafter_system_blocks("")
        assert len(blocks) == 1

    def test_tool_required_fields(self):
        schema = DRAFTER_TOOL["input_schema"]
        for k in ("body_text", "requires_action", "confidence"):
            assert k in schema["required"]


class TestDrafterUserMessage:
    def test_includes_category(self):
        msgs = build_drafter_messages(
            ticket_subject=None,
            ticket_body="Voucher nie działa.",
            category="voucher_redemption",
            cms_context=None,
        )
        text = msgs[0]["content"][0]["text"]
        assert "voucher_redemption" in text

    def test_includes_cms_context_when_provided(self):
        msgs = build_drafter_messages(
            ticket_subject="re",
            ticket_body="pytanie",
            category="voucher_redemption",
            cms_context="voucher_status: active",
        )
        text = msgs[0]["content"][0]["text"]
        assert "<cms_context>" in text
        assert "voucher_status: active" in text

    def test_omits_cms_block_when_none(self):
        msgs = build_drafter_messages(
            ticket_subject=None,
            ticket_body="pytanie",
            category="voucher_redemption",
            cms_context=None,
        )
        text = msgs[0]["content"][0]["text"]
        assert "<cms_context>" not in text

    def test_wraps_in_untrusted_tag(self):
        msgs = build_drafter_messages(
            ticket_subject="x",
            ticket_body="abc",
            category="other",
            cms_context=None,
        )
        text = msgs[0]["content"][0]["text"]
        assert "<untrusted_user_input>" in text


class TestRefundRule:
    def test_brand_voice_codifies_refund_blocking(self):
        # The drafter prompt itself should mention that refund tickets don't reach it,
        # so even if classification mis-routes, the model is reminded to escalate.
        assert "refund" in DRAFTER_SYSTEM.lower()
        assert "escalate" in DRAFTER_SYSTEM.lower() or "human" in DRAFTER_SYSTEM.lower()
