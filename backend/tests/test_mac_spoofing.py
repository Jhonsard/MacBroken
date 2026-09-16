"""
Tests unitaires du service MAC Spoofing (aucune dépendance Docker).
"""
from __future__ import annotations

import pytest

from app.services import mac_spoofing as ms


# ------------------------------------------------------------------
# Validation MAC
# ------------------------------------------------------------------
@pytest.mark.parametrize("mac", [
    "aa:bb:cc:dd:ee:ff",
    "02:11:22:33:44:55",
    "0a:00:00:00:00:01",
])
def test_valid_mac(mac: str) -> None:
    assert ms.is_valid_mac(mac) is True


@pytest.mark.parametrize("mac", [
    "zz:bb:cc:dd:ee:ff",       # hex invalide
    "aa:bb:cc:dd:ee",          # trop court
    "01:00:5e:00:00:01",       # multicast
    "ff:ff:ff:ff:ff:ff",       # broadcast
    "00:00:00:00:00:00",       # null
    "",
])
def test_invalid_mac(mac: str) -> None:
    assert ms.is_valid_mac(mac) is False


def test_locally_administered_bit() -> None:
    assert ms.is_locally_administered("02:00:00:00:00:00") is True
    assert ms.is_locally_administered("00:00:00:00:00:00") is False


def test_generate_random_mac() -> None:
    for _ in range(100):
        mac = ms.generate_random_mac()
        assert ms.is_valid_mac(mac)
        assert ms.is_locally_administered(mac)


def test_normalize_mac() -> None:
    assert ms.normalize_mac("AA-BB-CC-DD-EE-FF") == "aa:bb:cc:dd:ee:ff"
    assert ms.normalize_mac("AA:BB:CC:DD:EE:FF ") == "aa:bb:cc:dd:ee:ff"