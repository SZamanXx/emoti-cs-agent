"""Tests for the pricing math in llm/pricing.py.

These numbers are quoted in the brief and the JOURNEY. Any drift here is a credibility hole.
Verified against Anthropic public pricing, May 2026:
  - Haiku 4.5  : $1.00 / $5.00  per 1M tokens (input/output)
  - Sonnet 4.6 : $3.00 / $15.00 per 1M tokens
  - Cache write 5m: 1.25× input
  - Cache read    : 0.10× input
"""
from __future__ import annotations

import math

import pytest

from app.llm.pricing import PRICING, cost_for_call


HAIKU = "claude-haiku-4-5-20251001"
SONNET = "claude-sonnet-4-6"


class TestPricingTable:
    def test_haiku_input(self):
        assert PRICING[HAIKU]["input"] == 1.00

    def test_haiku_output(self):
        assert PRICING[HAIKU]["output"] == 5.00

    def test_haiku_cache_write_5m_is_1_25x_input(self):
        assert PRICING[HAIKU]["cache_write_5m"] == pytest.approx(1.25 * PRICING[HAIKU]["input"])

    def test_haiku_cache_read_is_0_10x_input(self):
        assert PRICING[HAIKU]["cache_read"] == pytest.approx(0.10 * PRICING[HAIKU]["input"])

    def test_sonnet_input(self):
        assert PRICING[SONNET]["input"] == 3.00

    def test_sonnet_output(self):
        assert PRICING[SONNET]["output"] == 15.00

    def test_sonnet_cache_write_5m_is_1_25x_input(self):
        assert PRICING[SONNET]["cache_write_5m"] == pytest.approx(1.25 * PRICING[SONNET]["input"])

    def test_sonnet_cache_write_1h_is_2x_input(self):
        assert PRICING[SONNET]["cache_write_1h"] == pytest.approx(2.0 * PRICING[SONNET]["input"])

    def test_sonnet_cache_read_is_0_10x_input(self):
        assert PRICING[SONNET]["cache_read"] == pytest.approx(0.10 * PRICING[SONNET]["input"])


class TestCostForCall:
    def test_unknown_model_returns_zero(self):
        assert cost_for_call("nonexistent-model", input_tokens=1_000_000, output_tokens=1_000_000) == 0.0

    def test_haiku_pure_input(self):
        # 1M input tokens on Haiku at $1.00/M = $1.00
        assert cost_for_call(HAIKU, input_tokens=1_000_000) == pytest.approx(1.00)

    def test_haiku_pure_output(self):
        assert cost_for_call(HAIKU, output_tokens=1_000_000) == pytest.approx(5.00)

    def test_sonnet_pure_output(self):
        assert cost_for_call(SONNET, output_tokens=1_000_000) == pytest.approx(15.00)

    def test_haiku_cached_is_10pct_of_input(self):
        # 1M cached-read tokens cost 0.10 × $1.00 = $0.10
        assert cost_for_call(HAIKU, cached_input_tokens=1_000_000) == pytest.approx(0.10)

    def test_haiku_cache_write_5m_is_125pct_of_input(self):
        # 1M cache-creation tokens at 5m TTL cost 1.25 × $1.00 = $1.25
        assert cost_for_call(HAIKU, cache_creation_tokens=1_000_000, cache_ttl="5m") == pytest.approx(1.25)

    def test_sonnet_cache_write_1h_is_2x_input(self):
        assert cost_for_call(SONNET, cache_creation_tokens=1_000_000, cache_ttl="1h") == pytest.approx(6.00)

    def test_combined_call_cost(self):
        # A realistic single drafter call:
        #   input = 500 tokens (fresh)
        #   cached_input = 5000 tokens (cache hit on the prefix)
        #   output = 250 tokens
        cost = cost_for_call(
            SONNET,
            input_tokens=500,
            cached_input_tokens=5000,
            output_tokens=250,
        )
        # 500 * $3/M = $0.0015
        # 5000 * $0.30/M = $0.0015
        # 250 * $15/M = $0.00375
        # total = ~$0.00675
        assert cost == pytest.approx(0.00675, abs=1e-6)

    def test_zero_call_is_zero(self):
        assert cost_for_call(SONNET) == 0.0


class TestForecastClaim:
    """Cross-check the headline claim — ~$0.89/day at 100 tickets/day, ~$27/month."""

    def test_daily_cost_in_expected_range(self):
        # Approximation from the brief — orders of magnitude must match.
        # Classifier per ticket: 1500 cached + 300 fresh in + 80 out (Haiku)
        # Judge per ticket: 1500 cached + 300 fresh in + 30 out (Haiku)
        # Drafter per ticket: 5500 cached + 500 fresh in + 250 out (Sonnet)
        per_ticket_classifier = cost_for_call(
            HAIKU, input_tokens=300, cached_input_tokens=1500, output_tokens=80
        )
        per_ticket_judge = cost_for_call(
            HAIKU, input_tokens=300, cached_input_tokens=1500, output_tokens=30
        )
        per_ticket_drafter = cost_for_call(
            SONNET, input_tokens=500, cached_input_tokens=5500, output_tokens=250
        )
        per_ticket_total = per_ticket_classifier + per_ticket_judge + per_ticket_drafter
        daily = per_ticket_total * 100
        assert 0.5 < daily < 1.5, f"daily forecast out of range: ${daily:.4f}"
        # Per-ticket cost should be in the "few grosza" range — ~3 grosza at 3.62 PLN/USD.
        per_ticket_pln_grosze = per_ticket_total * 3.62 * 100
        assert 1.0 < per_ticket_pln_grosze < 8.0, f"per-ticket grosze: {per_ticket_pln_grosze:.2f}"
