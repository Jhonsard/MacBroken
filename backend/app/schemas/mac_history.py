"""
Schémas Pydantic v2 pour l'historique MAC.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.mac_history import MacSpoofStatus

# Regex MAC : accepte aa:bb:cc:dd:ee:ff et aa-bb-cc-dd-ee-ff
MAC_PATTERN = r"^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$"
IFACE_PATTERN = r"^[A-Za-z0-9_.:-]{1,32}$"


class MacHistoryBase(BaseModel):
    interface_name: str = Field(
        ..., min_length=1, max_length=32, pattern=IFACE_PATTERN,
        examples=["eth0", "wlan0"],
    )
    original_mac: str = Field(..., pattern=MAC_PATTERN, examples=["aa:bb:cc:dd:ee:ff"])
    spoofed_mac: str = Field(..., pattern=MAC_PATTERN, examples=["02:11:22:33:44:55"])


class MacHistoryCreate(MacHistoryBase):
    pass


class MacHistoryRead(MacHistoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    status: MacSpoofStatus
    timestamp: datetime