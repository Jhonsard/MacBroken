"""
Service MAC Spoofing — primitives pures (aucune dépendance FastAPI/Celery).

Responsabilités :
  - Validation MAC (format + unicast + locally administered)
  - Génération MAC aléatoire conforme IEEE 802
  - Détection interfaces réseau via `ip -j link`
  - Vérification "spoofabilité" d'une interface (whitelist/blacklist)
  - Application / restauration MAC via `ip link set` (shell=False)
  - Mode DRY-RUN global (simulation sûre pour dev/tests)

⚠️ Toutes les commandes système passent par subprocess.run(list, shell=False)
   avec timeout strict. Aucune concaténation shell.
"""
from __future__ import annotations

import json
import logging
import random
import re
import subprocess
from dataclasses import dataclass
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Constantes
# ------------------------------------------------------------------
MAC_REGEX = re.compile(r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$")
IFACE_NAME_REGEX = re.compile(r"^[a-z][a-z0-9._-]{0,14}$")

# Blacklist d'interfaces : on ne touche JAMAIS à ces interfaces
IFACE_BLACKLIST_PREFIXES = (
    "lo", "docker", "br-", "veth", "virbr", "tun", "tap",
    "wg", "dummy", "sit", "bond", "vlan",
)

# MAC non valides (broadcast, multicast, null)
INVALID_MACS = {
    "ff:ff:ff:ff:ff:ff",
    "00:00:00:00:00:00",
    "01:00:5e:00:00:01",
}


# ------------------------------------------------------------------
# Exceptions métier
# ------------------------------------------------------------------
class MacSpoofError(Exception):
    """Erreur générique MAC spoofing."""


class InvalidMacError(MacSpoofError):
    """MAC fournie invalide."""


class InterfaceNotFoundError(MacSpoofError):
    """Interface inexistante."""


class InterfaceNotSpoofableError(MacSpoofError):
    """Interface protégée (blacklist, non-physique, etc.)."""


class SystemCommandError(MacSpoofError):
    """Échec d'une commande système (`ip`)."""


# ------------------------------------------------------------------
# Dataclass interface
# ------------------------------------------------------------------
@dataclass(slots=True, frozen=True)
class InterfaceInfo:
    name: str
    mac: str
    state: str          # "up" / "down" / "unknown"
    is_loopback: bool
    is_spoofable: bool
    reason: str         # raison si non-spoofable


# ------------------------------------------------------------------
# Validation / génération MAC
# ------------------------------------------------------------------
def is_valid_mac(mac: str) -> bool:
    """Format `aa:bb:cc:dd:ee:ff` en minuscules, unicast, non-null."""
    if not mac or not MAC_REGEX.match(mac):
        return False
    if mac in INVALID_MACS:
        return False
    first_octet = int(mac.split(":")[0], 16)
    # bit 0 = I/G (0 = unicast), bit 1 = U/L (0 = universel)
    # On accepte unicast uniquement ; U/L indifférent (spoofé = local).
    if first_octet & 0x01:      # multicast
        return False
    return True


def is_locally_administered(mac: str) -> bool:
    """Vrai si le bit U/L (bit 1 du 1er octet) est à 1."""
    first_octet = int(mac.split(":")[0], 16)
    return bool(first_octet & 0x02)


def generate_random_mac() -> str:
    """
    Génère une MAC valide, unicast, **locally administered** (pratique
    recommandée pour le spoofing : évite les collisions avec les OUI).
    """
    first_byte = (random.randint(0, 0xFF) & 0xFC) | 0x02   # unicast + local
    rest = [random.randint(0, 0xFF) for _ in range(5)]
    return ":".join(f"{b:02x}" for b in [first_byte, *rest])


def normalize_mac(mac: str) -> str:
    """Normalise en minuscules avec `:` comme séparateur."""
    return mac.replace("-", ":").lower().strip()


# ------------------------------------------------------------------
# Exécution commandes `ip`
# ------------------------------------------------------------------
def _run_ip(args: list[str], timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    """
    Exécute une commande `ip` de façon sûre.
    - shell=False (pas d'injection)
    - timeout strict
    - capture stdout/stderr
    """
    cmd = [settings.IP_BIN, *args]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=False,
            timeout=timeout or settings.MAC_SPOOF_CMD_TIMEOUT,
            check=False,
        )
    except FileNotFoundError as exc:
        raise SystemCommandError(f"Binaire `ip` introuvable ({settings.IP_BIN}).") from exc
    except subprocess.TimeoutExpired as exc:
        raise SystemCommandError(
            f"Timeout ({timeout or settings.MAC_SPOOF_CMD_TIMEOUT}s) sur : {' '.join(cmd)}",
        ) from exc

    if result.returncode != 0:
        raise SystemCommandError(
            f"Échec `ip {' '.join(args)}` (code {result.returncode}) : "
            f"{result.stderr.strip() or result.stdout.strip()}",
        )
    return result


# ------------------------------------------------------------------
# Détection interfaces
# ------------------------------------------------------------------
def _is_spoofable(name: str, mac: str, flags: list[str]) -> tuple[bool, str]:
    """Retourne (is_spoofable, reason)."""
    if not IFACE_NAME_REGEX.match(name):
        return False, "nom d'interface invalide"

    if any(name.startswith(prefix) for prefix in IFACE_BLACKLIST_PREFIXES):
        return False, "interface protégée (préfixe blacklist)"

    if "LOOPBACK" in flags:
        return False, "loopback"

    if not mac or mac == "00:00:00:00:00:00":
        return False, "pas d'adresse MAC"

    if not is_valid_mac(mac):
        return False, "MAC invalide"

    # ⚠️ En prod : exiger une whitelist explicite
    if settings.APP_ENV == "production" and not settings.ALLOWED_INTERFACES:
        return False, "ALLOWED_INTERFACES vide en production — refus par défaut"

    if settings.ALLOWED_INTERFACES and name not in settings.ALLOWED_INTERFACES:
        return False, "non listée dans ALLOWED_INTERFACES"

    return True, ""


def list_interfaces() -> list[InterfaceInfo]:
    """Liste les interfaces réseau via `ip -j link show`."""
    result = _run_ip(["-j", "link", "show"])
    try:
        raw: list[dict[str, Any]] = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SystemCommandError("Sortie `ip -j link show` non JSON.") from exc

    interfaces: list[InterfaceInfo] = []
    for entry in raw:
        name = entry.get("ifname", "")
        mac = normalize_mac(entry.get("address", ""))
        flags = entry.get("flags", [])
        operstate = entry.get("operstate", "unknown").lower()

        is_loopback = "LOOPBACK" in flags
        spoofable, reason = _is_spoofable(name, mac, flags)

        interfaces.append(
            InterfaceInfo(
                name=name,
                mac=mac,
                state=operstate,
                is_loopback=is_loopback,
                is_spoofable=spoofable,
                reason=reason,
            ),
        )
    return interfaces


def get_interface(name: str) -> InterfaceInfo:
    """Retourne une interface par nom, ou lève InterfaceNotFoundError."""
    for iface in list_interfaces():
        if iface.name == name:
            return iface
    raise InterfaceNotFoundError(f"Interface `{name}` introuvable.")


# ------------------------------------------------------------------
# Application / restauration MAC
# ------------------------------------------------------------------
def apply_mac(interface_name: str, new_mac: str) -> dict[str, Any]:
    """
    Change la MAC d'une interface.
    Séquence : down → set address → up.
    En mode DRY_RUN, simule et retourne un résultat synthétique.
    """
    if not is_valid_mac(new_mac):
        raise InvalidMacError(f"MAC invalide : {new_mac}")

    iface = get_interface(interface_name)
    if not iface.is_spoofable:
        raise InterfaceNotSpoofableError(
            f"Interface `{interface_name}` non spoofable ({iface.reason}).",
        )

    if settings.MAC_SPOOF_DRY_RUN:
        logger.warning(
            "[DRY-RUN] apply_mac(%s, %s) — aucune modification réelle.",
            interface_name, new_mac,
        )
        return {
            "dry_run": True,
            "interface": interface_name,
            "original_mac": iface.mac,
            "target_mac": new_mac,
        }

    logger.info("apply_mac(%s, %s) — down/set/up", interface_name, new_mac)
    _run_ip(["link", "set", "dev", interface_name, "down"])
    try:
        _run_ip(["link", "set", "dev", interface_name, "address", new_mac])
    finally:
        # Toujours remonter l'interface, même en cas d'échec du set
        _run_ip(["link", "set", "dev", interface_name, "up"])

    # Vérification : la MAC courante correspond-elle à la cible ?
    confirmed = get_interface(interface_name)
    if confirmed.mac != new_mac:
        raise SystemCommandError(
            f"MAC non appliquée sur `{interface_name}` "
            f"(attendu={new_mac}, obtenu={confirmed.mac}).",
        )

    return {
        "dry_run": False,
        "interface": interface_name,
        "original_mac": iface.mac,
        "target_mac": new_mac,
    }


def restore_mac(interface_name: str, original_mac: str) -> dict[str, Any]:
    """Restaure une MAC précédemment sauvegardée."""
    logger.info("restore_mac(%s, %s)", interface_name, original_mac)
    return apply_mac(interface_name, original_mac)