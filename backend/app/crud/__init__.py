"""Registre des modules CRUD."""
from app.crud import chat_log, mac_history, user

__all__ = ["user", "mac_history", "chat_log"]