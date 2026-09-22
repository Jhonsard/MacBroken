"""
Schémas Pydantic v2 pour l'historique MAC.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.mac_history import MacSpoofStatus
from app.services import mac_spoofing

# Regex MAC : format de base aa:bb:cc:dd:ee:ff (minuscules avec :)
MAC_PATTERN = r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$"
IFACE_PATTERN = r"^[a-z][a-z0-9._-]{0,14}$"


class MacHistoryBase(BaseModel):
    interface_name: str = Field(
        ..., min_length=1, max_length=32, pattern=IFACE_PATTERN,
        examples=["eth0", "wlan0"],
    )
    original_mac: str = Field(..., pattern=MAC_PATTERN, examples=["aa:bb:cc:dd:ee:ff"])
    spoofed_mac: str = Field(..., pattern=MAC_PATTERN, examples=["02:11:22:33:44:55"])

    @field_validator("original_mac", "spoofed_mac", mode="before")
    @classmethod
    def _validate_mac(cls, v: str) -> str:
        normalized = mac_spoofing.normalize_mac(v)
        if not mac_spoofing.is_valid_mac(normalized):
            raise ValueError("MAC invalide : doit être unicast, non-null, non-broadcast/multicast")
        return normalized


class MacHistoryCreate(MacHistoryBase):
    pass


class MacHistoryRead(MacHistoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    status: MacSpoofStatus
    timestamp: datetime