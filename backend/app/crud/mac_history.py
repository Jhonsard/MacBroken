"""
CRUD `mac_history` — utilisé par l'API et le worker Celery (Étape 3).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mac_history import MacHistory, MacSpoofStatus
from app.schemas.mac_history import MacHistoryCreate


async def create(
    db: AsyncSession, user_id: uuid.UUID, payload: MacHistoryCreate,
) -> MacHistory:
    entry = MacHistory(
        user_id=user_id,
        interface_name=payload.interface_name,
        original_mac=payload.original_mac.lower(),
        spoofed_mac=payload.spoofed_mac.lower(),
        status=MacSpoofStatus.PENDING,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


async def get_by_id(db: AsyncSession, entry_id: uuid.UUID) -> MacHistory | None:
    return await db.get(MacHistory, entry_id)


async def list_for_user(
    db: AsyncSession, user_id: uuid.UUID, limit: int = 100, offset: int = 0,
) -> list[MacHistory]:
    stmt = (
        select(MacHistory)
        .where(MacHistory.user_id == user_id)
        .order_by(MacHistory.timestamp.desc())
        .limit(limit)
        .offset(offset)
    )
    return list((await db.execute(stmt)).scalars().all())


async def set_status(
    db: AsyncSession, entry: MacHistory, status: MacSpoofStatus,
) -> MacHistory:
    entry.status = status
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


async def cleanup_stale_pending(
    db: AsyncSession, max_age_minutes: int = 5,
) -> int:
    """
    Supprime les entrées PENDING plus vieilles que max_age_minutes.
    Ces entrées sont orphelines (worker crash avant completion).
    Retourne le nombre d'entrées supprimées.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)
    stmt = delete(MacHistory).where(
        MacHistory.status == MacSpoofStatus.PENDING,
        MacHistory.timestamp < cutoff,
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount