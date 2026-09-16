"""
Modèle `users` — comptes utilisateurs de la plateforme.
"""
from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True,
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
    )

    # --- Relations ---
    mac_history: Mapped[list["MacHistory"]] = relationship(  # noqa: F821
        "MacHistory", back_populates="user",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    chat_logs: Mapped[list["ChatLog"]] = relationship(  # noqa: F821
        "ChatLog", back_populates="user",
        cascade="all, delete-orphan", passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"