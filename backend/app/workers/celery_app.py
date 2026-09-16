"""
Instance Celery — squelette minimal livré à l'Étape 2 pour éviter le
crash-loop du container `worker`. Sera enrichi à l'Étape 3 avec :
  - autodiscover_tasks
  - routing dédié par queue
  - timeouts stricts
  - hooks de télémétrie
"""
from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "mac_spoofing",
    broker=str(settings.CELERY_BROKER_URL),
    backend=str(settings.CELERY_RESULT_BACKEND),
)

# --- Configuration minimale (sûre dès maintenant) ---
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,                 # acquittement après exécution (fiabilité)
    worker_prefetch_multiplier=1,        # 1 tâche à la fois par slot (MAC = sensible)
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    # Sera complété à l'Étape 3 :
    # task_routes={...},
    # task_time_limit=30,
    # task_soft_time_limit=20,
)


@celery_app.task(name="app.workers.celery_app.ping")
def ping() -> str:
    """Tâche sentinelle — permet de vérifier que le worker répond."""
    return "pong"