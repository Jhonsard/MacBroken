"""
Schémas Pydantic v2 pour l'authentification.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.user import UserRead


class LoginRequest(BaseModel):
    """Payload de /auth/login (JSON)."""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=72)


class TokenPair(BaseModel):
    """Réponse standard : paire access + refresh."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Durée de vie de l'access token (secondes).")


class RefreshRequest(BaseModel):
    """Payload de /auth/refresh."""
    refresh_token: str = Field(..., min_length=10)


class LoginResponse(TokenPair):
    """Réponse de /auth/login — inclut le profil utilisateur."""
    user: UserRead


class MeResponse(UserRead):
    """Alias sémantique pour /auth/me."""
    pass