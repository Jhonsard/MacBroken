"""
Point d'entrée FastAPI — API Gateway de la plateforme MAC Spoofing.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import router as health_router
from app.core.config import settings

# --- Logging structuré ---
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("app")


def create_app() -> FastAPI:
    """Application factory — facilite les tests et le multi-env."""
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="Plateforme de MAC Spoofing sécurisée — API Gateway.",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
    )

    # --- CORS ---
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # --- Routers ---
    app.include_router(health_router, prefix="/api/v1")

    @app.on_event("startup")
    async def _on_startup() -> None:
        logger.info(
            "Démarrage %s (env=%s, debug=%s)",
            settings.APP_NAME, settings.APP_ENV, settings.DEBUG,
        )

    @app.on_event("shutdown")
    async def _on_shutdown() -> None:
        logger.info("Arrêt de l'application.")

    return app


app = create_app()