"""
Endpoints de santé — utilisés par Docker healthchecks et le load balancer.
"""
from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import check_db_connection

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness() -> dict[str, str]:
    """Liveness probe — le process est vivant."""
    return {"status": "ok", "service": settings.APP_NAME, "env": settings.APP_ENV}


@router.get("/ready")
async def readiness() -> JSONResponse:
    """
    Readiness probe — le service est prêt à recevoir du trafic.
    Vérifie la connectivité PostgreSQL.
    """
    db_ok = await check_db_connection()
    payload = {
        "status": "ok" if db_ok else "degraded",
        "checks": {"database": "ok" if db_ok else "unreachable"},
    }
    code = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=code, content=payload)