"""Point d'entrée FastAPI — API Gateway."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.mac import router as mac_router
from app.api.v1.chat import router as chat_router
from app.api.v1.ws import router as ws_router
from app.core.cache import close_redis
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.crud.mac_history import cleanup_stale_pending

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(
        "Démarrage %s (env=%s, debug=%s, dry_run=%s)",
        settings.APP_NAME, settings.APP_ENV, settings.DEBUG,
        settings.MAC_SPOOF_DRY_RUN,
    )
    # Cleanup stale PENDING entries on startup
    async with AsyncSessionLocal() as session:
        try:
            deleted = await cleanup_stale_pending(session, max_age_minutes=5)
            if deleted:
                logger.info("Nettoyage démarrage : %d entrées PENDING orphelines supprimées", deleted)
        except Exception as exc:
            logger.warning("Échec nettoyage entrées PENDING : %s", exc)
    yield
    await close_redis()
    logger.info("Arrêt de l'application.")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.3.0",
        description="Plateforme de MAC Spoofing sécurisée — API Gateway.",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(mac_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(ws_router, prefix="/api/v1")

    return app


app = create_app()
