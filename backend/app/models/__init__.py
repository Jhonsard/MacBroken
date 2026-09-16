"""
Registre central des modèles.
⚠️ Tout nouveau modèle DOIT être importé ici
   pour qu'Alembic autogénère correctement les migrations.
"""
from app.models.chat_log import ChatLog
from app.models.mac_history import MacHistory, MacSpoofStatus
from app.models.user import User

__all__ = ["User", "MacHistory", "MacSpoofStatus", "ChatLog"]