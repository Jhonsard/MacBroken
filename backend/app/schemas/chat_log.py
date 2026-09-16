"""
Schémas Pydantic v2 pour les logs du chatbot.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatLogBase(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    response: str = Field(..., min_length=1, max_length=32000)


class ChatLogCreate(ChatLogBase):
    pass


class ChatLogRead(ChatLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    timestamp: datetime