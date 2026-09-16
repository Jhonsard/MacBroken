"""
Modèle `mac_history` — journal des changements de MAC.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import utcnow


class MacSpoofStatus(str, enum.Enum):
    """Statuts possibles d'une opération de spoofing."""
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class MacHistory(Base):
    __tablename__ = "mac_history"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    interface_name: Mapped[str] = mapped_column(String(32), nullable=False)
    original_mac: Mapped[str] = mapped_column(String(17), nullable=False)
    spoofed_mac: Mapped[str] = mapped_column(String(17), nullable=False)
    status: Mapped[MacSpoofStatus] = mapped_column(
        Enum(MacSpoofStatus, name="mac_spoof_status", native_enum=True),
        default=MacSpoofStatus.PENDING,
        nullable=False,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="mac_history")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<MacHistory id={self.id} iface={self.interface_name} "
            f"status={self.status.value}>"
        )