"""
Gestion des sessions WebSocket actives + exécution des actions.
Une instance = un user connecté (une seule socket active à la fois par user).
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import chat_log as chat_crud
from app.crud import mac_history as mac_history_crud
from app.schemas.chat_log import ChatLogCreate
from app.services import mac_spoofing
from app.core.config import settings
from app.workers.tasks.mac_spoof import perform_mac_spoof

logger = logging.getLogger(__name__)


class ChatSession:
    """Session WebSocket d'un utilisateur."""

    def __init__(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        self.user_id = user_id
        self.ws = websocket
        self._send_lock = asyncio.Lock()

    async def send(self, payload: dict[str, Any]) -> None:
        """Envoi thread-safe (les actions async peuvent écrire en parallèle)."""
        async with self._send_lock:
            try:
                await self.ws.send_json(payload)
            except Exception as exc:  # noqa: BLE001
                logger.warning("WS send failed user=%s : %s", self.user_id, exc)

    async def log_exchange(self, db: AsyncSession, message: str, response: str) -> None:
        """Persiste l'échange dans chat_logs (best-effort)."""
        try:
            await chat_crud.create(
                db, self.user_id, ChatLogCreate(message=message, response=response),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Persistance chat_logs échouée : %s", exc)


# ------------------------------------------------------------------
# Registre global (1 process = OK ; multi-workers → Redis Pub/Sub à venir)
# ------------------------------------------------------------------
_sessions: dict[uuid.UUID, ChatSession] = {}


def register(session: ChatSession) -> None:
    _sessions[session.user_id] = session


def unregister(user_id: uuid.UUID) -> None:
    _sessions.pop(user_id, None)


def get(user_id: uuid.UUID) -> ChatSession | None:
    return _sessions.get(user_id)


# ------------------------------------------------------------------
# Exécution des actions (appelées depuis le handler WS)
# ------------------------------------------------------------------
async def execute_action(
    session: ChatSession,
    db: AsyncSession,
    action: str,
    params: dict[str, Any],
    action_id: uuid.UUID,
) -> dict[str, Any]:
    """
    Exécute une action confirmée et retourne un payload `action_result`.

    - list_interfaces : lecture seule
    - list_history    : lecture seule
    - status          : lecture seule
    - spoof           : enqueue Celery + polling
    """
    try:
        if action == "list_interfaces":
            ifaces = mac_spoofing.list_interfaces()
            lines = []
            for i in ifaces:
                state = "OK" if i.is_spoofable else f"NON ({i.reason})"
                lines.append(f"- `{i.name}` ({i.mac}) — {i.state} — {state}")
            text = "**Interfaces détectées**\n\n" + "\n".join(lines) if lines else "Aucune interface."
            return {
                "type": "action_result",
                "action_id": str(action_id),
                "success": True,
                "data": {"text": text},
            }

        if action == "list_history":
            limit = int(params.get("limit", 10))
            items = await mac_history_crud.list_for_user(db, session.user_id, limit=limit)
            if not items:
                text = "Aucun changement enregistré."
            else:
                lines = [
                    f"- `{it.timestamp:%Y-%m-%d %H:%M}` · `{it.interface_name}` · "
                    f"`{it.original_mac}` → `{it.spoofed_mac}` · **{it.status.value}**"
                    for it in items
                ]
                text = f"**Historique ({len(items)})**\n\n" + "\n".join(lines)
            return {
                "type": "action_result",
                "action_id": str(action_id),
                "success": True,
                "data": {"text": text},
            }

        if action == "status":
            text = (
                f"**État de la plateforme**\n\n"
                f"- Mode : `{'DRY-RUN' if settings.MAC_SPOOF_DRY_RUN else 'LIVE'}`\n"
                f"- Rate-limit : `{settings.MAC_SPOOF_RATE_LIMIT_SECONDS}s`\n"
                f"- Interface par défaut : `{settings.DEFAULT_INTERFACE}`"
            )
            return {
                "type": "action_result",
                "action_id": str(action_id),
                "success": True,
                "data": {"text": text},
            }

        if action == "spoof":
            iface = params["interface_name"]
            target_mac = params.get("spoofed_mac")

            # Validation interface
            try:
                info = mac_spoofing.get_interface(iface)
            except mac_spoofing.InterfaceNotFoundError as exc:
                return _error(action_id, str(exc))
            if not info.is_spoofable:
                return _error(action_id, f"Interface non spoofable : {info.reason}")

            # Détermine MAC cible
            if target_mac:
                normalized = mac_spoofing.normalize_mac(target_mac)
                if not mac_spoofing.is_valid_mac(normalized):
                    return _error(action_id, "MAC cible invalide.")
            else:
                normalized = mac_spoofing.generate_random_mac()

            if normalized == info.mac:
                return _error(action_id, "MAC cible identique à l'actuelle.")

            # Persiste + enqueue (réutilise le CRUD existant)
            entry = await mac_history_crud.create(
                db,
                user_id=session.user_id,
                payload=mac_history_crud.MacHistoryCreate(  # type: ignore[attr-defined]
                    interface_name=info.name,
                    original_mac=info.mac,
                    spoofed_mac=normalized,
                ),
            )
            async_result = perform_mac_spoof.apply_async(
                args=[str(entry.id)], queue="mac",
            )

            # Ack immédiat
            await session.send({
                "type": "action_result",
                "action_id": str(action_id),
                "success": True,
                "data": {
                    "text": (
                        f"Action enqueued pour `{info.name}`.\n\n"
                        f"- MAC cible : `{normalized}`\n"
                        f"- Task ID : `{async_result.id}`"
                    ),
                    "task_id": async_result.id,
                },
            })

            # Polling asynchrone du résultat
            asyncio.create_task(_poll_task(session, action_id, async_result.id))
            return {"_already_sent": True}

        return _error(action_id, f"Action inconnue : {action}")

    except Exception as exc:  # noqa: BLE001
        logger.exception("Erreur action %s", action)
        return _error(action_id, f"Erreur interne : {exc}")


def _error(action_id: uuid.UUID, message: str) -> dict[str, Any]:
    return {
        "type": "action_result",
        "action_id": str(action_id),
        "success": False,
        "error": message,
    }


async def _poll_task(session: ChatSession, action_id: uuid.UUID, task_id: str) -> None:
    """Suit l'exécution d'une tâche Celery et notifie le client à la fin."""
    from celery.result import AsyncResult

    from app.workers.celery_app import celery_app

    for _ in range(40):  # ~20 s max
        await asyncio.sleep(0.5)
        ar = AsyncResult(task_id, app=celery_app)
        if ar.ready():
            if ar.successful():
                result = ar.result if isinstance(ar.result, dict) else {"value": ar.result}
                await session.send({
                    "type": "action_result",
                    "action_id": str(action_id),
                    "success": True,
                    "data": {
                        "text": (
                            f"✅ Spoof terminé — "
                            f"`{result.get('original_mac')}` → `{result.get('spoofed_mac')}`"
                            f"{' (DRY-RUN)' if result.get('dry_run') else ''}"
                        ),
                        "task_result": result,
                    },
                })
            else:
                await session.send({
                    "type": "action_result",
                    "action_id": str(action_id),
                    "success": False,
                    "error": str(ar.result),
                })
            return
    await session.send({
        "type": "action_result",
        "action_id": str(action_id),
        "success": False,
        "error": "Timeout — la tâche n'a pas répondu à temps.",
    })
