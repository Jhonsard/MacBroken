"""
Tâche Celery `mac.spoof` — exécution réelle du spoofing.
Lit l'entrée `MacHistory`, applique la MAC, met à jour le statut.
En cas d'échec, tente une restauration automatique de l'original.
"""
from __future__ import annotations

import logging
import uuid

from celery.exceptions import SoftTimeLimitExceeded

from app.core.database import sync_session_scope
from app.models.mac_history import MacHistory, MacSpoofStatus
from app.services import mac_spoofing
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="mac.spoof",
    bind=True,
    max_retries=0,          # pas de retry auto : opération sensible
    acks_late=True,
)
def perform_mac_spoof(self, entry_id: str) -> dict:
    """
    Exécute le spoof pour l'entrée MacHistory donnée.

    Returns:
        dict : { ok, entry_id, status, original_mac, spoofed_mac, error }
    """
    entry_uuid = uuid.UUID(entry_id)
    logger.info("[task %s] Démarrage spoof entry=%s", self.request.id, entry_id)

    with sync_session_scope() as session:
        entry: MacHistory | None = session.get(MacHistory, entry_uuid)
        if entry is None:
            logger.error("Entry %s introuvable.", entry_id)
            return {"ok": False, "entry_id": entry_id, "error": "entry_not_found"}

        entry.status = MacSpoofStatus.PENDING
        session.add(entry)
        session.commit()

        original_mac = entry.original_mac
        target_mac = entry.spoofed_mac
        interface = entry.interface_name

        try:
            result = mac_spoofing.apply_mac(interface, target_mac)
            entry.status = MacSpoofStatus.SUCCESS
            session.add(entry)
            logger.info(
                "[task %s] SUCCESS iface=%s %s → %s (dry_run=%s)",
                self.request.id, interface, original_mac, target_mac,
                result.get("dry_run"),
            )
            return {
                "ok": True,
                "entry_id": entry_id,
                "status": entry.status.value,
                "interface": interface,
                "original_mac": original_mac,
                "spoofed_mac": target_mac,
                "dry_run": result.get("dry_run", False),
            }

        except SoftTimeLimitExceeded:
            logger.error("[task %s] SoftTimeLimitExceeded — rollback.", self.request.id)
            entry.status = MacSpoofStatus.FAILED
            session.add(entry)
            _try_restore(interface, original_mac)
            return {"ok": False, "entry_id": entry_id, "error": "timeout"}

        except mac_spoofing.MacSpoofError as exc:
            logger.error("[task %s] Échec métier : %s — rollback.", self.request.id, exc)
            entry.status = MacSpoofStatus.FAILED
            session.add(entry)
            _try_restore(interface, original_mac)
            return {"ok": False, "entry_id": entry_id, "error": str(exc)}

        except Exception as exc:  # noqa: BLE001
            logger.exception("[task %s] Exception inattendue.", self.request.id)
            entry.status = MacSpoofStatus.FAILED
            session.add(entry)
            _try_restore(interface, original_mac)
            return {"ok": False, "entry_id": entry_id, "error": f"unexpected: {exc}"}


def _try_restore(interface: str, original_mac: str) -> None:
    """Tente une restauration best-effort, log sans relever."""
    try:
        mac_spoofing.restore_mac(interface, original_mac)
        logger.info("Restauration OK : %s → %s", interface, original_mac)
    except Exception as exc:  # noqa: BLE001
        logger.error("Restauration échouée : %s", exc)