"""
Dépendances FastAPI partagées : session DB, utilisateur courant (JWT).
"""
from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db as _get_db
from app.core.security import TokenError, decode_token
from app.crud import user as user_crud
from app.models.user import User

# `tokenUrl` = endpoint utilisé par le bouton "Authorize" de Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=True)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Alias exposé aux routers (évite d'importer core.database partout)."""
    async for session in _get_db():
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Résout l'utilisateur à partir de l'access token Bearer."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token, expected_type="access")
        user_id = uuid.UUID(payload["sub"])
    except (TokenError, ValueError, KeyError) as exc:
        raise credentials_exc from exc

    user = await user_crud.get_by_id(db, user_id)
    if user is None:
        raise credentials_exc
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte utilisateur désactivé.",
        )
    return user