"""
Endpoints REST pour l'historique du chat (fallback si WebSocket indispo).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.crud import chat_log as chat_crud
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["Chat REST"])


@router.get("/history", summary="Historique paginé du chat")
async def history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    items = await chat_crud.list_for_user(db, current_user.id, limit=limit, offset=offset)
    return {
        "items": [
            {
                "id": str(it.id),
                "message": it.message,
                "response": it.response,
                "timestamp": it.timestamp.isoformat(),
            }
            for it in items
        ],
        "total": len(items),
        "limit": limit,
        "offset": offset,
    }
