from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import auth, health, inbound, kb, metrics, settings as settings_routes, tickets

_settings = get_settings()
logging.basicConfig(level=getattr(logging, _settings.log_level.upper(), logging.INFO))


def create_app() -> FastAPI:
    app = FastAPI(
        title="Emoti CS Agent API",
        version="0.1.0",
        description="Semi-autonomous customer-service agent. Inbound ticket -> classify -> draft -> human review -> send.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # demo only; lock down in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(tickets.router)
    app.include_router(inbound.router)
    app.include_router(kb.router)
    app.include_router(metrics.router)
    app.include_router(settings_routes.router)
    return app


app = create_app()
