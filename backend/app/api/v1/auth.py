"""
Endpoints d'authentification :
  POST /auth/register  — inscription
  POST /auth/login     — connexion JSON
  POST /auth/token     — connexion OAuth2 form (pour Swagger)
  POST /auth/refresh   — rotation du refresh token
  GET  /auth/me        — profil de l'utilisateur courant
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MeResponse,
    RefreshRequest,
    TokenPair,
)
from app.schemas.user import UserCreate, UserRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un compte utilisateur",
)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    return await auth_service.register_user(db, payload)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Connexion (JSON)",
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    return await auth_service.login(db, payload.username, payload.password)


@router.post(
    "/token",
    response_model=TokenPair,
    summary="Connexion (OAuth2 form — utilisé par Swagger UI)",
    include_in_schema=True,
)
async def token(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    result = await auth_service.login(db, form.username, form.password)
    return TokenPair(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type=result.token_type,
        expires_in=result.expires_in,
    )


@router.post(
    "/refresh",
    response_model=TokenPair,
    status_code=status.HTTP_200_OK,
    summary="Rafraîchir la paire de tokens",
)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    return await auth_service.refresh_tokens(db, payload.refresh_token)


@router.get(
    "/me",
    response_model=MeResponse,
    status_code=status.HTTP_200_OK,
    summary="Profil de l'utilisateur courant",
)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user