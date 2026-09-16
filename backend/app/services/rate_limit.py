"""
Rate-limiting basé sur Redis.

  - check_rate_limit  : consomme un slot (SET NX EX)
  - peek_rate_limit   : lecture seule (dry-run, affichage)
"""
from __future__ import annotations

import logging
import uuid

from app.core.cache import redis_client

logger = logging.getLogger(__name__)


def _key(user_id: uuid.UUID, action: str) -> str:
    return f"ratelimit:{action}:{user_id}"


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
    Lecture seule — n'altère PAS l'état du compteur.

    Retourne (available, retry_after_seconds) :
      - available=True  → aucune limite active
      - available=False → limite active, retry_after = TTL restant
    """
    key = _key(user_id, action)
    exists = await redis_client.exists(key)
    if not exists:
        return True, 0
    ttl = await redis_client.ttl(key)
    return False, max(ttl, 1)


async def reset_rate_limit(user_id: uuid.UUID, action: str) -> None:
    """Réinitialise le compteur (admin / tests)."""
    await redis_client.delete(_key(user_id, action))