"""Outbound webhook delivery (push drafts to consumer's URL) with HMAC + retry."""
from __future__ import annotations

import json

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.security.hmac_signing import sign

_settings = get_settings()


async def push_draft_ready(payload: dict) -> dict:
    if not _settings.outbound_webhook_url:
        return {"ok": False, "skipped": True, "reason": "no outbound webhook configured"}

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    secret = _settings.outbound_webhook_hmac_secret or _settings.webhook_hmac_secret
    signature = sign(secret, body)

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
    }

    last_error: str | None = None
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=False,
    ):
        with attempt:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(_settings.outbound_webhook_url, content=body, headers=headers)
                    if resp.status_code >= 500:
                        raise httpx.HTTPStatusError(
                            f"outbound 5xx: {resp.status_code}", request=resp.request, response=resp
                        )
                    return {"ok": resp.status_code < 400, "status": resp.status_code}
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_error = repr(exc)
                raise

    return {"ok": False, "error": last_error}
