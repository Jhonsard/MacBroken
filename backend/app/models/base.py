"""
Mixins réutilisables pour tous les modèles SQLAlchemy 2.0.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column


def utcnow() -> datetime:
    """Retourne un datetime timezone-aware en UTC."""
    return datetime.now(timezone.utc)


class UUIDMixin:
    """Ajoute une PK UUID v4 (native PostgreSQL)."""
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


class TimestampMixin:
    """Ajoute les colonnes created_at / updated_at (UTC)."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )