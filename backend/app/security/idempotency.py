from __future__ import annotations

from typing import Any

import redis.asyncio as redis

from app.config import get_settings

_settings = get_settings()
_pool: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _pool
    if _pool is None:
        _pool = redis.from_url(_settings.redis_url, decode_responses=True)
    return _pool


async def reserve_idempotency_key(key: str, payload_hash: str, ttl: int | None = None) -> tuple[bool, str | None]:
    if not key:
        return True, None
    r = await get_redis()
    redis_key = f"idem:{key}"
    set_ok = await r.set(redis_key, payload_hash, nx=True, ex=ttl or _settings.idempotency_ttl_seconds)
    if set_ok:
        return True, None
    existing = await r.get(redis_key)
    return False, existing


async def cache_get(key: str) -> Any | None:
    r = await get_redis()
    return await r.get(key)


async def cache_set(key: str, value: str, ttl: int | None = None) -> None:
    r = await get_redis()
    await r.set(key, value, ex=ttl or _settings.cache_ttl_seconds)
