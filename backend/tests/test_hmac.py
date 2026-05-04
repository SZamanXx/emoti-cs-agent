"""HMAC signing roundtrip + replay-protection window."""
from __future__ import annotations

import time

from app.security.hmac_signing import sign, verify


SECRET = "test-hmac-secret-32-bytes-min!!"


class TestSignVerifyRoundtrip:
    def test_roundtrip_simple(self):
        body = b'{"hello":"world"}'
        sig = sign(SECRET, body)
        assert verify(SECRET, body, sig)

    def test_wrong_secret_rejected(self):
        body = b'{"x":1}'
        sig = sign(SECRET, body)
        assert not verify("different-secret-32-bytes-pad!!!", body, sig)

    def test_modified_body_rejected(self):
        body = b'{"x":1}'
        tampered = b'{"x":2}'
        sig = sign(SECRET, body)
        assert not verify(SECRET, tampered, sig)

    def test_empty_signature_rejected(self):
        assert not verify(SECRET, b"x", "")

    def test_missing_v1_part_rejected(self):
        ts = str(int(time.time()))
        bad = f"t={ts}"  # no v1
        assert not verify(SECRET, b"x", bad)


class TestReplayProtection:
    def test_old_timestamp_rejected_default_window(self):
        body = b'{"x":1}'
        old_ts = str(int(time.time()) - 600)  # 10 min in the past
        sig = sign(SECRET, body, timestamp=old_ts)
        assert not verify(SECRET, body, sig, max_age_seconds=300)

    def test_old_timestamp_accepted_when_window_widened(self):
        body = b'{"x":1}'
        old_ts = str(int(time.time()) - 600)
        sig = sign(SECRET, body, timestamp=old_ts)
        assert verify(SECRET, body, sig, max_age_seconds=10_000)

    def test_future_timestamp_far_ahead_rejected(self):
        body = b'{"x":1}'
        future_ts = str(int(time.time()) + 600)
        sig = sign(SECRET, body, timestamp=future_ts)
        assert not verify(SECRET, body, sig, max_age_seconds=300)

    def test_unparseable_timestamp_rejected(self):
        sig = "t=notanumber,v1=abcd"
        assert not verify(SECRET, b"x", sig)


class TestSignFormat:
    def test_signature_format(self):
        sig = sign(SECRET, b"hello", timestamp="1234567890")
        assert sig.startswith("t=1234567890,v1=")
        digest = sig.split(",v1=")[1]
        assert len(digest) == 64  # sha256 hex
