"""
Schémas Pydantic v2 pour les utilisateurs.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.security import BCRYPT_MAX_BYTES

# --- Champs réutilisables (validation stricte) ---
USERNAME_PATTERN = r"^[A-Za-z0-9_]{3,50}$"


class UserBase(BaseModel):
    username: str = Field(
        ..., min_length=3, max_length=50, pattern=USERNAME_PATTERN,
        description="3-50 caractères, lettres/chiffres/underscore uniquement.",
        examples=["neo_42"],
    )
    email: EmailStr = Field(..., max_length=255, examples=["neo@example.com"])


class UserCreate(UserBase):
    """Payload d'inscription."""
    password: str = Field(
        ..., min_length=8, max_length=BCRYPT_MAX_BYTES,
        description=f"Min. 8 caractères, max {BCRYPT_MAX_BYTES} octets (bcrypt).",
    )


class UserRead(UserBase):
    """Représentation publique d'un utilisateur (jamais de hash)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    """Champs modifiables (PATCH)."""
    email: EmailStr | None = Field(default=None, max_length=255)
    password: str | None = Field(
        default=None, min_length=8, max_length=BCRYPT_MAX_BYTES,
    )