"""Registre des schémas Pydantic."""
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MeResponse,
    RefreshRequest,
    TokenPair,
)
from app.schemas.chat_log import ChatLogCreate, ChatLogRead
from app.schemas.mac_history import MacHistoryCreate, MacHistoryRead
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.schemas.mac import (
    CanSpoofRequest,
    CanSpoofResponse,
    InterfaceInfo,
    InterfaceListResponse,
    MacHistoryListResponse,
    SpoofRequest,
    SpoofResponse,
    TaskStatusResponse,
)

__all__ = [
    "UserCreate", "UserRead", "UserUpdate",
    "LoginRequest", "LoginResponse", "TokenPair", "RefreshRequest", "MeResponse",
    "MacHistoryCreate", "MacHistoryRead",
    "ChatLogCreate", "ChatLogRead",
    "CanSpoofRequest", "CanSpoofResponse",
    "InterfaceInfo", "InterfaceListResponse",
    "MacHistoryListResponse", "SpoofRequest", "SpoofResponse", "TaskStatusResponse",
]