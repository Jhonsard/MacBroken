"""
Schémas Pydantic v2 pour les endpoints MAC.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.mac_history import MacHistoryRead
from app.models.mac_history import MacSpoofStatus
from app.schemas.mac_validators import is_valid_mac, normalize_mac

MAC_PATTERN = r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$"
IFACE_PATTERN = r"^[a-z][a-z0-9._-]{0,14}$"


# ------------------------------------------------------------------
# Interfaces
# ------------------------------------------------------------------
class InterfaceInfo(BaseModel):
    name: str
    mac: str
    state: str
    is_loopback: bool
    is_spoofable: bool
    reason: str = ""


class InterfaceListResponse(BaseModel):
    interfaces: list[InterfaceInfo]
    dry_run: bool


# ------------------------------------------------------------------
# Dry-run (Q3)
# ------------------------------------------------------------------
class CanSpoofRequest(BaseModel):
    interface_name: str = Field(..., pattern=IFACE_PATTERN, examples=["eth0"])
    spoofed_mac: str | None = Field(default=None, pattern=MAC_PATTERN)

    @field_validator("spoofed_mac", mode="before")
    @classmethod
    def _validate_spoofed_mac(cls, v: str | None) -> str | None:
        if v is None:
            return v
        normalized = normalize_mac(v)
        if not is_valid_mac(normalized):
            raise ValueError("MAC invalide : doit être unicast, non-null, non-broadcast/multicast")
        return normalized


class CanSpoofResponse(BaseModel):
    allowed: bool
    interface_name: str
    current_mac: str | None = None
    target_mac: str | None = None
    reason: str = ""
    rate_limited: bool = False
    retry_after_seconds: int = 0


# ------------------------------------------------------------------
# Spoof
# ------------------------------------------------------------------
class SpoofRequest(BaseModel):
    interface_name: str = Field(..., pattern=IFACE_PATTERN, examples=["eth0"])
    spoofed_mac: str | None = Field(
        default=None, pattern=MAC_PATTERN,
        description="Laisser vide pour générer une MAC aléatoire locally-administered.",
    )

    @field_validator("spoofed_mac", mode="before")
    @classmethod
    def _validate_spoofed_mac(cls, v: str | None) -> str | None:
        if v is None:
            return v
        normalized = normalize_mac(v)
        if not is_valid_mac(normalized):
            raise ValueError("MAC invalide : doit être unicast, non-null, non-broadcast/multicast")
        return normalized


class SpoofResponse(BaseModel):
    task_id: str = Field(..., description="ID de la tâche Celery")
    entry_id: uuid.UUID = Field(..., description="ID de l'entrée MacHistory créée")
    interface_name: str
    original_mac: str
    spoofed_mac: str
    status: MacSpoofStatus


# ------------------------------------------------------------------
# Task status
# ------------------------------------------------------------------
class TaskStatusResponse(BaseModel):
    task_id: str
    state: str                    # PENDING / STARTED / SUCCESS / FAILURE
    ready: bool
    successful: bool | None = None
    result: dict | None = None
    error: str | None = None


# ------------------------------------------------------------------
# History (réutilise MacHistoryRead)
# ------------------------------------------------------------------
class MacHistoryListResponse(BaseModel):
    items: list[MacHistoryRead]
    total: int
    limit: int
    offset: int

MacHistoryListResponse.model_rebuild()