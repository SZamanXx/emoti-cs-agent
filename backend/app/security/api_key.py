"""Auth dependency: accept JWT bearer token OR legacy X-Api-Key header.

Returns the authenticated subject (JWT `sub` claim, the API key string itself, or "anonymous"
if auth is fully disabled in env).
"""
from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.config import get_settings
from app.security.jwt import verify_token


async def require_api_key(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> str:
    settings = get_settings()

    # 1. JWT bearer (preferred)
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        claims = verify_token(token)
        if claims and claims.get("sub"):
            return str(claims["sub"])
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired bearer token")

    # 2. Legacy X-Api-Key (service-to-service)
    if not settings.api_key:
        return "anonymous"
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing or invalid credentials (use Authorization: Bearer <jwt> or X-Api-Key)",
        )
    return f"apikey:{x_api_key[:6]}…"
