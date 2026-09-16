"""
Service d'authentification — orchestre CRUD + tokens.
Découplé des endpoints : testable et réutilisable (ex. refresh côté worker).
"""
from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.crud import user as user_crud
from app.models.user import User
from app.schemas.auth import LoginResponse, TokenPair
from app.schemas.user import UserCreate


async def register_user(db: AsyncSession, payload: UserCreate) -> User:
    """Inscription — vérifie l'unicité username/email avant création."""
    if await user_crud.get_by_username(db, payload.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ce nom d'utilisateur est déjà pris.",
        )
    if await user_crud.get_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cet email est déjà enregistré.",
        )
    return await user_crud.create(db, payload)


def _build_token_pair(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user.id, extra_claims={"username": user.username}),
        refresh_token=create_refresh_token(user.id),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def login(db: AsyncSession, username: str, password: str) -> LoginResponse:
    """Authentifie et retourne access + refresh + profil."""
    user = await user_crud.authenticate(db, username, password)
    if user is None:
        # Message volontairement générique (anti-énumération)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    pair = _build_token_pair(user)
    return LoginResponse(**pair.model_dump(), user=user)


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> TokenPair:
    """Échange un refresh token valide contre une nouvelle paire."""
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalide ou expiré.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    try:
        user_id = uuid.UUID(payload["sub"])
    except (ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Subject du token invalide.",
        ) from exc

    user = await user_crud.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable ou désactivé.",
        )

    return _build_token_pair(user)