"""
Client Redis async (rate-limiting, cache, verrous distribués).
"""
from __future__ import annotations

from redis.asyncio import Redis

from app.core.config import settings

redis_client: Redis = Redis.from_url(
    str(settings.CELERY_BROKER_URL),
    encoding="utf-8",
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
    health_check_interval=30,
)


async def close_redis() -> None:
    """Ferme proprement le pool de connexions (appelé au shutdown)."""
    await redis_client.aclose()


async def ping() -> bool:
    """Vérifie la connectivité Redis."""
    try:
        return await redis_client.ping()
    except Exception:
        return False