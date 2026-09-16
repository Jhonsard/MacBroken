"""
Endpoints MAC Spoofing.

  GET  /mac/interfaces           — liste les interfaces disponibles
  POST /mac/can-spoof            — dry-run Q3 (validation + rate-limit)
  POST /mac/spoof                — crée une entrée + enqueue Celery
  GET  /mac/history              — historique utilisateur
  GET  /mac/tasks/{task_id}      — statut d'une tâche Celery
"""
from __future__ import annotations

from dataclasses import asdict
import logging
from typing import Annotated, Any, cast

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.core.config import settings
from app.crud import mac_history as mac_history_crud
from app.models.mac_history import MacSpoofStatus
from app.models.user import User
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
from app.schemas.mac_history import MacHistoryCreate, MacHistoryRead
from app.services import mac_spoofing, rate_limit
from app.workers.celery_app import celery_app
from app.workers.tasks.mac_spoof import perform_mac_spoof

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mac", tags=["MAC Spoofing"])

RATE_LIMIT_ACTION = "mac_spoof"
CurrentUser = Annotated[User, Depends(get_current_user)]
Database = Annotated[AsyncSession, Depends(get_db)]


def _get_spoofable_interface(interface_name: str):
    try:
        iface = mac_spoofing.get_interface(interface_name)
    except mac_spoofing.InterfaceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if not iface.is_spoofable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Interface non spoofable : {iface.reason}",
        )
    return iface


def _get_target_mac(spoofed_mac: str | None) -> str:
    if not spoofed_mac:
        return mac_spoofing.generate_random_mac()

    target_mac = mac_spoofing.normalize_mac(spoofed_mac)
    if not mac_spoofing.is_valid_mac(target_mac):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="MAC cible invalide.",
        )
    return target_mac


# ------------------------------------------------------------------
# 1. Lister les interfaces
# ------------------------------------------------------------------
@router.get(
    "/interfaces",
    response_model=InterfaceListResponse,
    summary="Liste les interfaces réseau détectées",
)
async def list_interfaces(
    _: User = Depends(get_current_user),
) -> InterfaceListResponse:
    try:
        ifaces = mac_spoofing.list_interfaces()
    except mac_spoofing.SystemCommandError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Impossible de lister les interfaces : {exc}",
        ) from exc

    return InterfaceListResponse(
        interfaces=[InterfaceInfo(**asdict(iface)) for iface in ifaces],
        dry_run=settings.MAC_SPOOF_DRY_RUN,
    )

# ------------------------------------------------------------------
# 2. Dry-run Q3
# ------------------------------------------------------------------
@router.post(
    "/can-spoof",
    response_model=CanSpoofResponse,
    summary="Vérifie si un spoof est possible (dry-run)",
)
async def can_spoof(
    payload: CanSpoofRequest,
    current_user: User = Depends(get_current_user),
) -> CanSpoofResponse:
    # Rate-limit check
    allowed, retry_after = await rate_limit.peek_rate_limit(
    current_user.id, RATE_LIMIT_ACTION,
    )
    if not allowed:
        return CanSpoofResponse(
            allowed=False,
            interface_name=payload.interface_name,
            reason=f"Rate-limit actif ({settings.MAC_SPOOF_RATE_LIMIT_SECONDS}s).",
            rate_limited=True,
            retry_after_seconds=retry_after,
        )

    # Validation interface
    try:
        iface = mac_spoofing.get_interface(payload.interface_name)
    except mac_spoofing.InterfaceNotFoundError:
        return CanSpoofResponse(
            allowed=False,
            interface_name=payload.interface_name,
            reason="Interface introuvable.",
        )

    if not iface.is_spoofable:
        return CanSpoofResponse(
            allowed=False,
            interface_name=iface.name,
            current_mac=iface.mac,
            reason=iface.reason or "Interface non spoofable.",
        )

    # Cible : fournie ou générée
    target_mac = payload.spoofed_mac
    if target_mac is None:
        target_mac = mac_spoofing.generate_random_mac()
    else:
        target_mac = mac_spoofing.normalize_mac(target_mac)
        if not mac_spoofing.is_valid_mac(target_mac):
            return CanSpoofResponse(
                allowed=False,
                interface_name=iface.name,
                current_mac=iface.mac,
                reason="MAC cible invalide.",
            )

    return CanSpoofResponse(
        allowed=True,
        interface_name=iface.name,
        current_mac=iface.mac,
        target_mac=target_mac,
        reason="OK",
    )


# ------------------------------------------------------------------
# 3. Spoof (enqueue Celery)
# ------------------------------------------------------------------
@router.post(
    "/spoof",
    response_model=SpoofResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Déclenche un changement de MAC",
)
async def spoof(
    payload: SpoofRequest,
    current_user: CurrentUser,
    db: Database,
) -> SpoofResponse:
    # Rate-limit
    allowed, retry_after = await rate_limit.check_rate_limit(
        current_user.id, RATE_LIMIT_ACTION, settings.MAC_SPOOF_RATE_LIMIT_SECONDS,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Trop de requêtes — réessayez dans {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )

    iface = _get_spoofable_interface(payload.interface_name)
    target_mac = _get_target_mac(payload.spoofed_mac)

    if target_mac == iface.mac:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La MAC cible est identique à la MAC actuelle.",
        )

    # Q5 — Persiste l'original avant chaque spoof
    entry = await mac_history_crud.create(
        db,
        user_id=current_user.id,
        payload=MacHistoryCreate(
            interface_name=iface.name,
            original_mac=iface.mac,
            spoofed_mac=target_mac,
        ),
    )

    # Enqueue Celery
    task = cast(Any, perform_mac_spoof)
    async_result = task.apply_async(args=[str(entry.id)], queue="mac")
    logger.info(
        "Spoof enqueued user=%s entry=%s task=%s iface=%s %s→%s",
        current_user.username, entry.id, async_result.id,
        iface.name, iface.mac, target_mac,
    )

    return SpoofResponse(
        task_id=async_result.id,
        entry_id=entry.id,
        interface_name=iface.name,
        original_mac=iface.mac,
        spoofed_mac=target_mac,
        status=MacSpoofStatus.PENDING,
    )


# ------------------------------------------------------------------
# 4. Historique
# ------------------------------------------------------------------
@router.get(
    "/history",
    response_model=MacHistoryListResponse,
    summary="Historique des changements MAC de l'utilisateur",
)
async def history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MacHistoryListResponse:
    items = await mac_history_crud.list_for_user(
        db, current_user.id, limit=limit, offset=offset,
    )
    return MacHistoryListResponse(
        items=[MacHistoryRead.model_validate(i) for i in items],
        total=len(items), limit=limit, offset=offset,
    )


# ------------------------------------------------------------------
# 5. Statut tâche Celery
# ------------------------------------------------------------------
@router.get(
    "/tasks/{task_id}",
    response_model=TaskStatusResponse,
    summary="Statut d'une tâche Celery",
)
async def task_status(
    task_id: str,
    _: User = Depends(get_current_user),
) -> TaskStatusResponse:
    ar = AsyncResult(task_id, app=celery_app)
    result: dict | None = None
    error: str | None = None

    if ar.ready():
        if ar.successful():
            result = ar.result if isinstance(ar.result, dict) else {"value": ar.result}
        else:
            error = str(ar.result) if ar.result else "task failed"

    return TaskStatusResponse(
        task_id=task_id,
        state=ar.state,
        ready=ar.ready(),
        successful=ar.successful() if ar.ready() else None,
        result=result,
        error=error,
    )