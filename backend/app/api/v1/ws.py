"""
WebSocket endpoint : /api/v1/ws/chat?token=<JWT>

Protocole :
  - Le client envoie des frames JSON (ClientMessage | ClientConfirmAction).
  - Le serveur répond avec des frames JSON (ServerMessage | ActionRequest | ActionResult | …).

Auth :
  - Le token JWT est passé en query param (les WebSocket navigateur
    n'acceptent pas de header Authorization custom).
  - À la connexion, le serveur charge l'historique (Q8a) et l'envoie.
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.api.v1.deps import get_db
from app.core.database import AsyncSessionLocal
from app.core.security import TokenError, decode_token
from app.crud import chat_log as chat_crud
from app.crud import user as user_crud
from app.schemas.chat import ClientConfirmAction, ClientMessage
from app.services import chat_engine, chat_session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Chat WebSocket"])

HISTORY_LIMIT = 50  # Q8(a)


async def _authenticate(token: str) -> uuid.UUID | None:
    """Vérifie le JWT, retourne l'user_id ou None."""
    try:
        payload = decode_token(token, expected_type="access")
        return uuid.UUID(payload["sub"])
    except (TokenError, ValueError, KeyError):
        return None


@router.websocket("/ws/chat")
async def chat_ws(
    websocket: WebSocket,
    token: str = Query(..., min_length=10),
) -> None:
    user_id = await _authenticate(token)
    if user_id is None:
        await websocket.close(code=4401, reason="Unauthorized")
        return

    # Vérifier que l'utilisateur existe et est actif
    async with AsyncSessionLocal() as db:
        user = await user_crud.get_by_id(db, user_id)
        if user is None or not user.is_active:
            await websocket.close(code=4403, reason="Forbidden")
            return

    await websocket.accept()
    session = chat_session.ChatSession(user_id=user_id, websocket=websocket)
    chat_session.register(session)

    try:
        # --- 1. Charger l'historique (Q8a) ---
        async with AsyncSessionLocal() as db:
            history = await chat_crud.list_for_user(db, user_id, limit=HISTORY_LIMIT)
        # On renvoie du plus ancien au plus récent pour affichage naturel
        history_messages = []
        for h in reversed(history):
            history_messages.append({
                "role": "user",
                "content": h.message,
                "timestamp": h.timestamp.isoformat(),
            })
            history_messages.append({
                "role": "bot",
                "content": h.response,
                "timestamp": h.timestamp.isoformat(),
            })
        await session.send({"type": "history", "messages": history_messages})

        # --- 2. Message d'accueil ---
        await session.send({
            "type": "message",
            "id": str(uuid.uuid4()),
            "role": "bot",
            "content": (
                f"Bonjour **{user.username}** 👋\n\n"
                "Je suis votre assistant MAC Spoofing. Tapez `/help` pour voir "
                "les commandes disponibles."
            ),
            "timestamp": None,
        })

        # --- 3. Boucle de réception ---
        while True:
            raw = await websocket.receive_json()
            await _handle_frame(session, raw)

    except WebSocketDisconnect:
        logger.info("WS déconnecté user=%s", user_id)
    except Exception:
        logger.exception("WS erreur user=%s", user_id)
        try:
            await websocket.close(code=1011)
        except Exception:  # noqa: BLE001
            pass
    finally:
        chat_session.unregister(user_id)


async def _handle_frame(session: chat_session.ChatSession, raw: dict) -> None:
    """Dispatch d'une frame entrante."""
    ftype = raw.get("type")

    if ftype == "message":
        try:
            frame = ClientMessage.model_validate(raw)
        except ValidationError as exc:
            await session.send({"type": "error", "message": f"Frame invalide : {exc.errors()[0]['msg']}"})
            return
        await _handle_user_message(session, frame.content)

    elif ftype == "confirm_action":
        try:
            frame = ClientConfirmAction.model_validate(raw)
        except ValidationError as exc:
            await session.send({"type": "error", "message": f"Frame invalide : {exc.errors()[0]['msg']}"})
            return
        await _handle_confirmation(session, frame)

    else:
        await session.send({"type": "error", "message": f"Type de frame inconnu : {ftype}"})


async def _handle_user_message(session: chat_session.ChatSession, content: str) -> None:
    """Traite un message utilisateur via le moteur rule-based."""
    # Typing ON
    await session.send({"type": "typing", "state": "on"})

    engine_resp = chat_engine.respond(content)

    if engine_resp.kind == "text":
        await session.send({"type": "typing", "state": "off"})
        await session.send({
            "type": "message",
            "id": str(uuid.uuid4()),
            "role": "bot",
            "content": engine_resp.content,
            "timestamp": None,
        })
        async with AsyncSessionLocal() as db:
            await session.log_exchange(db, content, engine_resp.content)
            await db.commit()

    elif engine_resp.kind == "error":
        await session.send({"type": "typing", "state": "off"})
        await session.send({
            "type": "message",
            "id": str(uuid.uuid4()),
            "role": "bot",
            "content": f"⚠️ {engine_resp.content}",
            "timestamp": None,
        })
    elif engine_resp.kind == "action":
        if engine_resp.action in ("list_interfaces", "list_history", "status"):
            async with AsyncSessionLocal() as db:
                result = await chat_session.execute_action(
                    session, db, engine_resp.action, engine_resp.params, uuid.uuid4(),
                )
                await db.commit()
            await session.send({"type": "typing", "state": "off"})
            await session.send(result)
            if result.get("data", {}).get("text"):
                async with AsyncSessionLocal() as db:
                    await session.log_exchange(db, content, result["data"]["text"])
                    await db.commit()
        else:
            action_id = uuid.uuid4()
            # Mémorise l'action en attente de confirmation
            pending = getattr(session, "_pending_actions", None)
            if pending is None:
                pending = {}
                session._pending_actions = pending  # type: ignore[attr-defined]
            pending[str(action_id)] = (engine_resp.action, engine_resp.params)

            await session.send({"type": "typing", "state": "off"})
            await session.send({
                "type": "action_request",
                "action_id": str(action_id),
                "action": engine_resp.action,
                "params": engine_resp.params,
                "summary": engine_resp.summary,
                "requires_confirmation": True,
            })

async def _handle_confirmation(
    session: chat_session.ChatSession,
    frame: ClientConfirmAction,
) -> None:
    """Exécute ou annule une action confirmée."""
    if not frame.accept:
        await session.send({
            "type": "message",
            "id": str(uuid.uuid4()),
            "role": "bot",
            "content": "Action annulée.",
            "timestamp": None,
        })
        return

    # Reconstruire les paramètres depuis la frame d'origine n'est pas nécessaire :
    # le client envoie l'action + params dans la frame de confirmation.
    action = frame.action if hasattr(frame, "action") else None
    params = frame.params if hasattr(frame, "params") else {}

    # NOTE : notre ClientConfirmAction ne contient que action_id + accept.
    # Pour simplifier, on stocke l'action + params en cache côté serveur
    # (dict en mémoire via session).
    # ⚠️ À remplacer par un cache Redis en prod multi-instance.
    pending = getattr(session, "_pending_actions", None)
    if pending is None:
        pending = {}
        session._pending_actions = pending  # type: ignore[attr-defined]

    action = pending.pop(str(frame.action_id), None)
    if action is None:
        await session.send({
            "type": "error",
            "message": "Action expirée ou introuvable.",
        })
        return

    action_name, action_params = action
    await session.send({"type": "typing", "state": "on"})
    async with AsyncSessionLocal() as db:
        result = await chat_session.execute_action(
            session, db, action_name, action_params, frame.action_id,
        )
        await db.commit()
    await session.send({"type": "typing", "state": "off"})
    if not result.get("_already_sent"):
        await session.send(result)
