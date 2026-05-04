"""JWT bearer token issuance and verification.

Production-grade auth: a `/auth/login` endpoint trades a username + password (demo: from env)
for a signed JWT. All operator-console endpoints accept either a JWT bearer token OR a legacy
X-Api-Key header (kept for service-to-service callers that haven't migrated yet).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.config import get_settings

JWT_ALGO = "HS256"
JWT_DEFAULT_TTL_HOURS = 24


def _secret() -> str:
    s = get_settings()
    # In production this should be a separate, longer secret. For the demo we reuse the HMAC
    # webhook secret as the JWT signing key — it is a 256-bit shared secret either way.
    return s.webhook_hmac_secret


def issue_token(*, subject: str, role: str = "operator", ttl_hours: int = JWT_DEFAULT_TTL_HOURS) -> str:
    now = datetime.now(timezone.utc)
    claims: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=ttl_hours)).timestamp()),
        "iss": "emoti-cs-agent",
    }
    return jwt.encode(claims, _secret(), algorithm=JWT_ALGO)


def verify_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, _secret(), algorithms=[JWT_ALGO], issuer="emoti-cs-agent")
    except JWTError:
        return None
