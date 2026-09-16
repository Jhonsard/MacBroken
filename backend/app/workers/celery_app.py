"""
Instance Celery — routing, timeouts, autodiscover.
"""
from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "mac_spoofing",
    broker=str(settings.CELERY_BROKER_URL),
    backend=str(settings.CELERY_RESULT_BACKEND),
    include=["app.workers.tasks.mac_spoof"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,

    # --- Timeouts stricts (MAC = opération sensible) ---
    task_time_limit=settings.MAC_SPOOF_CMD_TIMEOUT * 6,        # hard kill (30 s)
    task_soft_time_limit=settings.MAC_SPOOF_CMD_TIMEOUT * 4,   # SoftTimeLimit (20 s)

    # --- Routing ---
    task_routes={
        "mac.spoof": {"queue": "mac"},
        "mac.restore": {"queue": "mac"},
    },
    task_default_queue="default",
)


@celery_app.task(name="app.workers.celery_app.ping")
def ping() -> str:
    """Sentinelle — vérifie que le worker répond."""
    return "pong"