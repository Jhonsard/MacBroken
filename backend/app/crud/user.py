"""
CRUD `users` — opérations async SQLAlchemy 2.0.
"""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.get(User, user_id)


async def get_by_username(db: AsyncSession, username: str) -> User | None:
    stmt = select(User).where(func.lower(User.username) == username.lower())
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(func.lower(User.email) == email.lower())
    return (await db.execute(stmt)).scalar_one_or_none()


async def create(db: AsyncSession, payload: UserCreate) -> User:
    """Crée un utilisateur (le hash est fait ici, jamais côté appelant)."""
    user = User(
        username=payload.username,
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    await db.flush()      # récupère l'id généré sans commit
    await db.refresh(user)
    return user


async def update(db: AsyncSession, user: User, payload: UserUpdate) -> User:
    data = payload.model_dump(exclude_unset=True)
    if "email" in data and data["email"] is not None:
        user.email = data["email"].lower()
    if "password" in data and data["password"] is not None:
        user.hashed_password = hash_password(data["password"])
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def authenticate(
    db: AsyncSession, username: str, password: str,
) -> User | None:
    """Vérifie les credentials — retourne le User ou None."""
    user = await get_by_username(db, username)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user