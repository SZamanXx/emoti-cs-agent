from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "Emoti CS Agent API",
        "docs": "/docs",
        "health": "/health",
    }
