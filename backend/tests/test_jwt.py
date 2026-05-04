"""JWT issuance + verification."""
from __future__ import annotations

import time

import pytest

from app.security.jwt import JWT_DEFAULT_TTL_HOURS, issue_token, verify_token


class TestIssueAndVerify:
    def test_basic_roundtrip(self):
        token = issue_token(subject="operator")
        claims = verify_token(token)
        assert claims is not None
        assert claims["sub"] == "operator"
        assert claims["role"] == "operator"
        assert claims["iss"] == "emoti-cs-agent"

    def test_role_propagated(self):
        token = issue_token(subject="alice", role="supervisor")
        claims = verify_token(token)
        assert claims is not None
        assert claims["role"] == "supervisor"

    def test_default_ttl(self):
        before = int(time.time())
        token = issue_token(subject="x")
        claims = verify_token(token)
        assert claims is not None
        ttl_seconds = claims["exp"] - claims["iat"]
        assert ttl_seconds == JWT_DEFAULT_TTL_HOURS * 3600

    def test_short_ttl_token_expires(self):
        # Issue a token with effectively no TTL.
        # We re-implement a hand-rolled short-lived token via ttl_hours fractional value
        # (issue_token uses hours, but timedelta accepts fractions).
        # NOTE: issue_token signature uses int hours; we test with 0 → already-expired.
        token = issue_token(subject="x", ttl_hours=0)
        # At ttl_hours=0, exp == iat, so any clock skew or even same-second decode should reject.
        # We poll briefly to be safe in case the test runs in the same epoch second.
        time.sleep(1.1)
        assert verify_token(token) is None

    def test_tampered_token_rejected(self):
        token = issue_token(subject="x")
        tampered = token[:-4] + "AAAA" if not token.endswith("AAAA") else token[:-4] + "BBBB"
        assert verify_token(tampered) is None

    def test_garbage_rejected(self):
        assert verify_token("not.a.real.jwt") is None
        assert verify_token("") is None
        assert verify_token("...") is None

    def test_iat_and_exp_present(self):
        token = issue_token(subject="x")
        claims = verify_token(token)
        assert claims is not None
        assert "iat" in claims
        assert "exp" in claims
        assert claims["exp"] > claims["iat"]
