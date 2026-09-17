"""
Schémas Pydantic v2 pour le chat temps réel (WebSocket).
Toutes les frames transitent en JSON structuré.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Frames client → serveur
# ------------------------------------------------------------------
class ClientMessage(BaseModel):
    type: Literal["message"] = "message"
    content: str = Field(..., min_length=1, max_length=2000)


class ClientConfirmAction(BaseModel):
    type: Literal["confirm_action"] = "confirm_action"
    action_id: uuid.UUID
    accept: bool


ClientFrame = ClientMessage | ClientConfirmAction


# ------------------------------------------------------------------
# Frames serveur → client
# ------------------------------------------------------------------
class ServerMessage(BaseModel):
    type: Literal["message"] = "message"
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    role: Literal["bot", "system"] = "bot"
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=None))


class ServerTyping(BaseModel):
    type: Literal["typing"] = "typing"
    state: Literal["on", "off"]


class ActionRequest(BaseModel):
    type: Literal["action_request"] = "action_request"
    action_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    action: str
    params: dict[str, Any]
    summary: str
    requires_confirmation: bool = True


class ActionResult(BaseModel):
    type: Literal["action_result"] = "action_result"
    action_id: uuid.UUID
    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


class ServerHistory(BaseModel):
    type: Literal["history"] = "history"
    messages: list[dict[str, Any]]


class ServerError(BaseModel):
    type: Literal["error"] = "error"
    message: str


ServerFrame = ServerMessage | ServerTyping | ActionRequest | ActionResult | ServerHistory | ServerError
