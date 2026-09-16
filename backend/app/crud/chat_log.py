"""
CRUD `chat_logs` — utilisé par le service chatbot (Étape 5).
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_log import ChatLog
from app.schemas.chat_log import ChatLogCreate


async def create(
    db: AsyncSession, user_id: uuid.UUID, payload: ChatLogCreate,
) -> ChatLog:
    entry = ChatLog(user_id=user_id, message=payload.message, response=payload.response)
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


async def list_for_user(
    db: AsyncSession, user_id: uuid.UUID, limit: int = 100, offset: int = 0,
) -> list[ChatLog]:
    stmt = (
        select(ChatLog)
        .where(ChatLog.user_id == user_id)
        .order_by(ChatLog.timestamp.desc())
        .limit(limit)
        .offset(offset)
    )
    return list((await db.execute(stmt)).scalars().all())