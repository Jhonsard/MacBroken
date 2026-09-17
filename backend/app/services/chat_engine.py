"""
Moteur rule-based du chatbot.

Pipeline :
  1. Normalise le message.
  2. Parse en commande (`/cmd args`) ou langage naturel.
  3. Produit une réponse (`Response`) qui peut être :
     - texte simple
     - demande de confirmation pour une action
     - erreur d'usage

Aucune dépendance FastAPI / DB : pur, testable.
"""
from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field
from typing import Any, Literal

# ------------------------------------------------------------------
# Types de sortie
# ------------------------------------------------------------------
ResponseKind = Literal["text", "action", "error"]


@dataclass(slots=True)
class EngineResponse:
    kind: ResponseKind
    content: str                                    # texte à afficher
    action: str | None = None                       # nom d'action (si kind=action)
    params: dict[str, Any] = field(default_factory=dict)
    summary: str = ""                               # résumé pour la carte de confirmation


# ------------------------------------------------------------------
# Helpers de parsing
# ------------------------------------------------------------------
IFACE_REGEX = re.compile(r"^[a-z][a-z0-9._-]{0,14}$")
MAC_REGEX = re.compile(r"^([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}$")


def _parse_args(raw: str) -> list[str]:
    """Parse les args façon shell (gère les quotes)."""
    try:
        return shlex.split(raw)
    except ValueError:
        return raw.split()


# ------------------------------------------------------------------
# Commandes disponibles
# ------------------------------------------------------------------
HELP_TEXT = """**Commandes disponibles**

- `/help` — affiche cette aide
- `/interfaces` — liste les interfaces réseau détectées
- `/spoof <interface> [mac]` — change la MAC (demande confirmation)
- `/history` — 10 derniers changements
- `/status` — état de la plateforme (dry-run, rate-limit)
- `/cancel` — annule l'action en attente

Vous pouvez aussi écrire en langage naturel : « liste mes interfaces », « montre mon historique »…"""


# ------------------------------------------------------------------
# Dispatcher
# ------------------------------------------------------------------
def respond(message: str) -> EngineResponse:
    """Point d'entrée unique : transforme un message en réponse."""
    raw = message.strip()
    if not raw:
        return EngineResponse(kind="error", content="Message vide.")

    # --- Commande slash ---
    if raw.startswith("/"):
        return _handle_command(raw)

    # --- Langage naturel (fuzzy matching) ---
    return _handle_natural(raw.lower())


def _handle_command(raw: str) -> EngineResponse:
    parts = _parse_args(raw)
    cmd = parts[0].lower()
    args = parts[1:]

    if cmd in ("/help", "/h", "/?"):
        return EngineResponse(kind="text", content=HELP_TEXT)

    if cmd == "/interfaces":
        return EngineResponse(
            kind="action",
            content="Je récupère la liste des interfaces…",
            action="list_interfaces",
            params={},
            summary="Lister les interfaces réseau détectées",
        )

    if cmd == "/spoof":
        if not args:
            return EngineResponse(
                kind="error",
                content="Usage : `/spoof <interface> [mac]`. Exemple : `/spoof eth0`.",
            )
        iface = args[0].lower().strip()
        if not IFACE_REGEX.match(iface):
            return EngineResponse(kind="error", content=f"Nom d'interface invalide : `{iface}`.")
        target_mac: str | None = None
        if len(args) >= 2:
            mac = args[1].lower().strip()
            if not MAC_REGEX.match(mac):
                return EngineResponse(kind="error", content=f"MAC invalide : `{mac}`.")
            target_mac = mac
        summary = (
            f"Changer la MAC de `{iface}` vers `{target_mac}`"
            if target_mac
            else f"Changer la MAC de `{iface}` vers une valeur aléatoire"
        )
        return EngineResponse(
            kind="action",
            content="Confirmez-vous cette action ?",
            action="spoof",
            params={"interface_name": iface, "spoofed_mac": target_mac},
            summary=summary,
        )

    if cmd == "/history":
        return EngineResponse(
            kind="action",
            content="Je récupère votre historique…",
            action="list_history",
            params={"limit": 10},
            summary="Afficher vos 10 derniers changements MAC",
        )

    if cmd == "/status":
        return EngineResponse(
            kind="action",
            content="Je vérifie l'état de la plateforme…",
            action="status",
            params={},
            summary="Afficher l'état (dry-run, rate-limit, worker)",
        )

    if cmd == "/cancel":
        return EngineResponse(kind="text", content="Aucune action en attente.")

    return EngineResponse(
        kind="error",
        content=f"Commande inconnue : `{cmd}`. Tapez `/help` pour la liste.",
    )


def _handle_natural(lower: str) -> EngineResponse:
    """Matching approximatif sur mots-clés."""
    if any(k in lower for k in ("interface", "iface", "carte réseau", "carte reseau")):
        return _handle_command("/interfaces")
    if any(k in lower for k in ("historique", "history", "log", "journal")):
        return _handle_command("/history")
    if any(k in lower for k in ("status", "état", "etat", "statut")):
        return _handle_command("/status")
    if any(k in lower for k in ("aide", "help", "commande", "que peux-tu")):
        return _handle_command("/help")
    if "spoof" in lower or "change" in lower and "mac" in lower:
        return EngineResponse(
            kind="text",
            content="Pour changer une MAC, utilisez : `/spoof <interface> [mac]`.",
        )

    return EngineResponse(
        kind="text",
        content=(
            "Je n'ai pas compris. Tapez `/help` pour voir les commandes, "
            "ou essayez « liste mes interfaces », « montre mon historique »…"
        ),
    )
