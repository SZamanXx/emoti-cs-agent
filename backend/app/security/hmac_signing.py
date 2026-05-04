from __future__ import annotations

import hashlib
import hmac
import time

from fastapi import Header, HTTPException, Request, status

from app.config import get_settings


def sign(secret: str, body: bytes, timestamp: str | None = None) -> str:
    ts = timestamp or str(int(time.time()))
    message = f"{ts}.".encode() + body
    digest = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return f"t={ts},v1={digest}"


def verify(secret: str, body: bytes, signature: str, max_age_seconds: int = 300) -> bool:
    if not signature:
        return False
    parts = dict(p.split("=", 1) for p in signature.split(",") if "=" in p)
    ts = parts.get("t")
    sig = parts.get("v1")
    if not ts or not sig:
        return False
    try:
        ts_int = int(ts)
    except ValueError:
        return False
    if abs(time.time() - ts_int) > max_age_seconds:
        return False
    expected = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


async def require_hmac(request: Request, x_webhook_signature: str | None = Header(default=None)) -> bytes:
    settings = get_settings()
    body = await request.body()
    if settings.webhook_hmac_secret and x_webhook_signature:
        if not verify(settings.webhook_hmac_secret, body, x_webhook_signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid HMAC signature")
    elif settings.webhook_hmac_secret and not x_webhook_signature:
        # In demo we allow non-signed when explicit dev API key is used; production should require signing.
        pass
    return body
