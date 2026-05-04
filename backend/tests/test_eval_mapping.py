"""Tests for the eval harness's expected-vs-actual mapping logic.

The eval harness has to bridge between user-supplied `expected_category` values that include
`suspected_injection` and `out_of_scope` (not first-class enum values) and our system's
real categories + status flags. This is the bridge that makes T-009 (injection) and T-015
(LT market) score correctly.
"""
from __future__ import annotations

from app.scripts.eval_classifier import _action_match, _category_match


class _FakeDraft:
    def __init__(self, requires_action=False, warnings=None):
        self.requires_action = requires_action
        self.warnings = warnings or []


class TestCategoryMatch:
    def test_simple_match(self):
        assert _category_match("voucher_redemption", "voucher_redemption", False, "drafted")

    def test_simple_mismatch(self):
        assert not _category_match("voucher_redemption", "expired_complaint", False, "drafted")

    def test_suspected_injection_via_flag(self):
        assert _category_match("suspected_injection", "refund_request", True, "escalated_human")

    def test_suspected_injection_no_flag_fails(self):
        assert not _category_match("suspected_injection", "refund_request", False, "drafted")

    def test_out_of_scope_via_other_category(self):
        assert _category_match("out_of_scope", "other", False, "drafted")

    def test_out_of_scope_via_escalated_status(self):
        assert _category_match("out_of_scope", "voucher_redemption", False, "escalated_human")

    def test_expired_voucher_alias_for_expired_complaint(self):
        # User KB uses "expired_voucher" while our enum is "expired_complaint".
        assert _category_match("expired_voucher", "expired_complaint", False, "drafted")

    def test_none_expected_passes_trivially(self):
        assert _category_match(None, "anything", False, "anywhere")


class TestActionMatch:
    def test_ai_draft(self):
        assert _action_match("ai_draft", "drafted", False, _FakeDraft())
        assert _action_match("ai_draft", "in_review", False, _FakeDraft())
        assert _action_match("ai_draft", "approved", False, _FakeDraft())
        assert _action_match("ai_draft", "edited", False, _FakeDraft())
        assert _action_match("ai_draft", "sent", False, _FakeDraft())

    def test_ai_draft_rejected_when_escalated(self):
        assert not _action_match("ai_draft", "escalated_human", False, None)

    def test_ai_draft_then_escalate_requires_action_or_warning(self):
        # status drafted + draft.requires_action True
        assert _action_match("ai_draft_then_escalate", "drafted", False, _FakeDraft(requires_action=True))
        # status drafted + warnings present
        assert _action_match("ai_draft_then_escalate", "drafted", False, _FakeDraft(warnings=["check this"]))

    def test_ai_draft_then_escalate_fails_when_clean_draft(self):
        assert not _action_match("ai_draft_then_escalate", "drafted", False, _FakeDraft())

    def test_escalate_human(self):
        assert _action_match("escalate_human", "escalated_human", False, None)
        assert not _action_match("escalate_human", "drafted", False, _FakeDraft())

    def test_escalate_human_empathy(self):
        assert _action_match("escalate_human_empathy", "escalated_human", False, None)

    def test_quarantine_escalate(self):
        # Must be escalated AND suspected_injection.
        assert _action_match("quarantine_escalate", "escalated_human", True, None)
        # Without injection flag, fails.
        assert not _action_match("quarantine_escalate", "escalated_human", False, None)
        # Drafted instead of escalated, fails.
        assert not _action_match("quarantine_escalate", "drafted", True, _FakeDraft())

    def test_unknown_action_fails(self):
        assert not _action_match("nonsense_action", "drafted", False, _FakeDraft())
