"""
Validateurs MAC partagés — sans dépendances circulaires.
Ce module ne doit importer que la stdlib.
"""
from __future__ import annotations

import re

# Constantes identiques à app/services/mac_spoofing.py
MAC_REGEX = re.compile(r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$")
INVALID_MACS = {
    "ff:ff:ff:ff:ff:ff",
    "00:00:00:00:00:00",
    "01:00:5e:00:00:01",
}


def normalize_mac(mac: str) -> str:
    """Normalise en minuscules avec `:` comme séparateur."""
    return mac.replace("-", ":").lower().strip()


def is_valid_mac(mac: str) -> bool:
    """Format `aa:bb:cc:dd:ee:ff` en minuscules, unicast, non-null."""
    if not mac or not MAC_REGEX.match(mac):
        return False
    if mac in INVALID_MACS:
        return False
    first_octet = int(mac.split(":")[0], 16)
    # bit 0 = I/G (0 = unicast)
    if first_octet & 0x01:
        return False
    return True