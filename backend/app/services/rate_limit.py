"""
Rate-limiting basé sur Redis.

  - check_rate_limit  : consomme un slot (SET NX EX)
  - peek_rate_limit   : lecture seule atomique via Lua (GET + TTL)
"""
from __future__ import annotations

import logging
import uuid

from app.core.cache import redis_client

logger = logging.getLogger(__name__)

# Lua script for atomic peek: returns [exists, ttl]
_PEEK_SCRIPT = """
local key = KEYS[1]
local exists = redis.call('EXISTS', key)
if exists == 0 then
    return {0, 0}
end
local ttl = redis.call('TTL', key)
return {1, ttl}
"""
_peek_sha: str | None = None


def _key(user_id: uuid.UUID, action: str) -> str:
    return f"ratelimit:{action}:{user_id}"


async def _get_peek_sha() -> str:
    global _peek_sha
    if _peek_sha is None:
        _peek_sha = await redis_client.script_load(_PEEK_SCRIPT)
    return _peek_sha


async def check_rate_limit(
    user_id: uuid.UUID,
    action: str,
    window_seconds: int,
) -> tuple[bool, int]:
    """
    Consomme un slot. Retourne (allowed, retry_after_seconds).

    - `allowed=True`  → la clé vient d'être posée, action autorisée
    - `allowed=False` → clé déjà présente, retourne le TTL restant
    """
    key = _key(user_id, action)
    was_set = await redis_client.set(key, "1", nx=True, ex=window_seconds)
    if was_set:
        return True, 0
    ttl = await redis_client.ttl(key)
    return False, max(ttl, 1)


async def peek_rate_limit(
    user_id: uuid.UUID,
    action: str,
) -> tuple[bool, int]:
    """
    Lecture seule atomique — n'altère PAS l'état du compteur.

    Retourne (available, retry_after_seconds) :
      - available=True  → aucune limite active
      - available=False → limite active, retry_after = TTL restant
    """
    key = _key(user_id, action)
    sha = await _get_peek_sha()
    try:
        result = await redis_client.evalsha(sha, 1, key)
    except Exception:
        # Fallback si script flushé (ex: Redis restart)
        exists = await redis_client.exists(key)
        if not exists:
            return True, 0
        ttl = await redis_client.ttl(key)
        return False, max(ttl, 1)

    exists = result[0]
    ttl = result[1]
    if exists == 0:
        return True, 0
    return False, max(ttl, 1)


async def reset_rate_limit(user_id: uuid.UUID, action: str) -> None:
    """Réinitialise le compteur (admin / tests)."""
    await redis_client.delete(_key(user_id, action))