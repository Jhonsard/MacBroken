"""Tests unitaires du moteur rule-based."""
from __future__ import annotations

import pytest

from app.services import chat_engine


def test_help_command() -> None:
    r = chat_engine.respond("/help")
    assert r.kind == "text"
    assert "/interfaces" in r.content


def test_interfaces_command() -> None:
    r = chat_engine.respond("/interfaces")
    assert r.kind == "action"
    assert r.action == "list_interfaces"


def test_spoof_no_args() -> None:
    r = chat_engine.respond("/spoof")
    assert r.kind == "error"
    assert "Usage" in r.content


def test_spoof_valid() -> None:
    r = chat_engine.respond("/spoof eth0")
    assert r.kind == "action"
    assert r.action == "spoof"
    assert r.params["interface_name"] == "eth0"
    assert r.params["spoofed_mac"] is None


def test_spoof_with_mac() -> None:
    r = chat_engine.respond("/spoof eth0 aa:bb:cc:dd:ee:ff")
    assert r.kind == "action"
    assert r.params["spoofed_mac"] == "aa:bb:cc:dd:ee:ff"


def test_spoof_invalid_iface() -> None:
    r = chat_engine.respond("/spoof ETH0!!")
    assert r.kind == "error"


def test_spoof_invalid_mac() -> None:
    r = chat_engine.respond("/spoof eth0 notamc")
    assert r.kind == "error"


def test_natural_interfaces() -> None:
    r = chat_engine.respond("liste mes interfaces")
    assert r.action == "list_interfaces"


def test_unknown() -> None:
    r = chat_engine.respond("bonjour")
    assert r.kind == "text"
    assert "/help" in r.content
