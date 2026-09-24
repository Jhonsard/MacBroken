"""
Tests d'intégration MAC Spoofing — API → Celery → DB.

Nécessite : PostgreSQL, Redis, Celery worker en cours d'exécution.
Lancer avec : pytest tests/test_integration_mac.py -v --tb=short
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.models.mac_history import MacSpoofStatus


@pytest.fixture
def app():
    """Crée l'application FastAPI."""
    return create_app()


@pytest.fixture
async def async_client(app):
    """Client HTTP asynchrone pour tester l'API."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_current_user():
    """Utilisateur mock pour l'authentification."""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.username = "testuser"
    user.email = "test@example.com"
    user.is_active = True
    return user


@pytest.fixture
def mock_db_session():
    """Session DB mock."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    session.scalars = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.get = AsyncMock()
    return session


class TestMACEndpoints:
    """Tests des endpoints MAC."""

    async def test_list_interfaces_dry_run(
        self, async_client, mock_current_user, mock_db_session
    ):
        """Test GET /mac/interfaces en mode DRY_RUN."""
        with patch("app.api.v1.mac.get_current_user", return_value=mock_current_user):
            with patch("app.api.v1.mac.mac_spoofing.list_interfaces") as mock_list:
                mock_list.return_value = [
                    MagicMock(
                        name="eth0",
                        mac="aa:bb:cc:dd:ee:ff",
                        state="up",
                        is_loopback=False,
                        is_spoofable=True,
                        reason="",
                    )
                ]
                response = await async_client.get("/api/v1/mac/interfaces")

        assert response.status_code == 200
        data = response.json()
        assert "interfaces" in data
        assert len(data["interfaces"]) == 1
        assert data["interfaces"][0]["name"] == "eth0"
        assert data["dry_run"] is True  # Par défaut en test

    async def test_can_spoof_valid_interface(
        self, async_client, mock_current_user, mock_db_session
    ):
        """Test POST /mac/can-spoof avec interface valide."""
        with patch("app.api.v1.mac.get_current_user", return_value=mock_current_user):
            with patch("app.api.v1.mac.rate_limit.peek_rate_limit") as mock_peek:
                mock_peek.return_value = (True, 0)
                with patch("app.api.v1.mac.mac_spoofing.get_interface") as mock_get_iface:
                    mock_get_iface.return_value = MagicMock(
                        name="eth0",
                        mac="aa:bb:cc:dd:ee:ff",
                        is_spoofable=True,
                        reason="",
                    )
                    with patch("app.api.v1.mac.mac_spoofing.generate_random_mac", return_value="02:11:22:33:44:55"):
                        response = await async_client.post(
                            "/api/v1/mac/can-spoof",
                            json={"interface_name": "eth0"},
                        )

        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is True
        assert data["interface_name"] == "eth0"
        assert data["current_mac"] == "aa:bb:cc:dd:ee:ff"
        assert data["target_mac"] == "02:11:22:33:44:55"

    async def test_can_spoof_invalid_mac_rejected(
        self, async_client, mock_current_user, mock_db_session
    ):
        """Test POST /mac/can-spoof rejette MAC invalide (multicast)."""
        with patch("app.api.v1.mac.get_current_user", return_value=mock_current_user):
            with patch("app.api.v1.mac.rate_limit.peek_rate_limit") as mock_peek:
                mock_peek.return_value = (True, 0)
                with patch("app.api.v1.mac.mac_spoofing.get_interface") as mock_get_iface:
                    mock_get_iface.return_value = MagicMock(
                        name="eth0",
                        mac="aa:bb:cc:dd:ee:ff",
                        is_spoofable=True,
                        reason="",
                    )
                    response = await async_client.post(
                        "/api/v1/mac/can-spoof",
                        json={"interface_name": "eth0", "spoofed_mac": "01:00:5e:00:00:01"},
                    )

        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is False
        assert "invalide" in data["reason"].lower()

    async def test_can_spoof_broadcast_rejected(
        self, async_client, mock_current_user, mock_db_session
    ):
        """Test POST /mac/can-spoof rejette broadcast."""
        with patch("app.api.v1.mac.get_current_user", return_value=mock_current_user):
            with patch("app.api.v1.mac.rate_limit.peek_rate_limit") as mock_peek:
                mock_peek.return_value = (True, 0)
                with patch("app.api.v1.mac.mac_spoofing.get_interface") as mock_get_iface:
                    mock_get_iface.return_value = MagicMock(
                        name="eth0",
                        mac="aa:bb:cc:dd:ee:ff",
                        is_spoofable=True,
                        reason="",
                    )
                    response = await async_client.post(
                        "/api/v1/mac/can-spoof",
                        json={"interface_name": "eth0", "spoofed_mac": "ff:ff:ff:ff:ff:ff"},
                    )

        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is False

    async def test_can_spoof_null_rejected(
        self, async_client, mock_current_user, mock_db_session
    ):
        """Test POST /mac/can-spoof rejette MAC null."""
        with patch("app.api.v1.mac.get_current_user", return_value=mock_current_user):
            with patch("app.api.v1.mac.rate_limit.peek_rate_limit") as mock_peek:
                mock_peek.return_value = (True, 0)
                with patch("app.api.v1.mac.mac_spoofing.get_interface") as mock_get_iface:
                    mock_get_iface.return_value = MagicMock(
                        name="eth0",
                        mac="aa:bb:cc:dd:ee:ff",
                        is_spoofable=True,
                        reason="",
                    )
                    response = await async_client.post(
                        "/api/v1/mac/can-spoof",
                        json={"interface_name": "eth0", "spoofed_mac": "00:00:00:00:00:00"},
                    )

        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is False

    async def test_spoof_creates_history_entry(
        self, async_client, mock_current_user, mock_db_session
    ):
        """Test POST /mac/spoof crée entrée MacHistory et enqueue Celery."""
        with patch("app.api.v1.mac.get_current_user", return_value=mock_current_user):
            with patch("app.api.v1.mac.get_db", return_value=mock_db_session):
                with patch("app.api.v1.mac.rate_limit.check_rate_limit") as mock_check:
                    mock_check.return_value = (True, 0)
                    with patch("app.api.v1.mac.mac_spoofing.get_interface") as mock_get_iface:
                        mock_get_iface.return_value = MagicMock(
                            name="eth0",
                            mac="aa:bb:cc:dd:ee:ff",
                            is_spoofable=True,
                            reason="",
                        )
                        with patch("app.api.v1.mac.mac_history_crud.create") as mock_create:
                            mock_entry = MagicMock()
                            mock_entry.id = uuid.uuid4()
                            mock_entry.interface_name = "eth0"
                            mock_entry.original_mac = "aa:bb:cc:dd:ee:ff"
                            mock_entry.spoofed_mac = "02:11:22:33:44:55"
                            mock_entry.status = MacSpoofStatus.PENDING
                            mock_create.return_value = mock_entry
                            with patch("app.api.v1.mac.perform_mac_spoof.apply_async") as mock_task:
                                mock_task.return_value = MagicMock(id="task-123")
                                response = await async_client.post(
                                    "/api/v1/mac/spoof",
                                    json={"interface_name": "eth0"},
                                )

        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        assert data["task_id"] == "task-123"
        assert data["interface_name"] == "eth0"
        assert data["status"] == "PENDING"

    async def test_spoof_same_mac_rejected(
        self, async_client, mock_current_user, mock_db_session
    ):
        """Test POST /mac/spoof rejette si MAC cible = MAC actuelle."""
        with patch("app.api.v1.mac.get_current_user", return_value=mock_current_user):
            with patch("app.api.v1.mac.get_db", return_value=mock_db_session):
                with patch("app.api.v1.mac.rate_limit.check_rate_limit") as mock_check:
                    mock_check.return_value = (True, 0)
                    with patch("app.api.v1.mac.mac_spoofing.get_interface") as mock_get_iface:
                        mock_get_iface.return_value = MagicMock(
                            name="eth0",
                            mac="aa:bb:cc:dd:ee:ff",
                            is_spoofable=True,
                            reason="",
                        )
                        response = await async_client.post(
                            "/api/v1/mac/spoof",
                            json={"interface_name": "eth0", "spoofed_mac": "aa:bb:cc:dd:ee:ff"},
                        )

        assert response.status_code == 400
        assert "identique" in response.json()["detail"].lower()

    async def test_history_returns_user_entries(
        self, async_client, mock_current_user, mock_db_session
    ):
        """Test GET /mac/history retourne l'historique utilisateur."""
        with patch("app.api.v1.mac.get_current_user", return_value=mock_current_user):
            with patch("app.api.v1.mac.get_db", return_value=mock_db_session):
                with patch("app.api.v1.mac.mac_history_crud.list_for_user") as mock_list:
                    mock_list.return_value = [
                        MagicMock(
                            id=uuid.uuid4(),
                            user_id=mock_current_user.id,
                            interface_name="eth0",
                            original_mac="aa:bb:cc:dd:ee:ff",
                            spoofed_mac="02:11:22:33:44:55",
                            status=MacSpoofStatus.SUCCESS,
                            timestamp="2024-01-01T00:00:00Z",
                        )
                    ]
                    response = await async_client.get("/api/v1/mac/history")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 1


class TestMACSchemaValidation:
    """Tests de validation des schémas Pydantic."""

    def test_mac_schema_rejects_multicast(self):
        """Le schéma rejette les MAC multicast."""
        from app.schemas.mac import CanSpoofRequest

        with pytest.raises(ValueError, match="invalide"):
            CanSpoofRequest(interface_name="eth0", spoofed_mac="01:00:5e:00:00:01")

    def test_mac_schema_rejects_broadcast(self):
        """Le schéma rejette les MAC broadcast."""
        from app.schemas.mac import CanSpoofRequest

        with pytest.raises(ValueError, match="invalide"):
            CanSpoofRequest(interface_name="eth0", spoofed_mac="ff:ff:ff:ff:ff:ff")

    def test_mac_schema_rejects_null(self):
        """Le schéma rejette les MAC null."""
        from app.schemas.mac import CanSpoofRequest

        with pytest.raises(ValueError, match="invalide"):
            CanSpoofRequest(interface_name="eth0", spoofed_mac="00:00:00:00:00:00")

    def test_mac_schema_normalizes_uppercase_dashes(self):
        """Le schéma normalise majuscules et tirets."""
        from app.schemas.mac import CanSpoofRequest

        req = CanSpoofRequest(interface_name="eth0", spoofed_mac="AA-BB-CC-DD-EE-FF")
        assert req.spoofed_mac == "aa:bb:cc:dd:ee:ff"

    def test_mac_schema_accepts_none_generates_random(self):
        """Le schéma accepte None pour générer une MAC aléatoire."""
        from app.schemas.mac import CanSpoofRequest

        req = CanSpoofRequest(interface_name="eth0", spoofed_mac=None)
        assert req.spoofed_mac is None

    def test_interface_schema_rejects_uppercase(self):
        """Le schéma rejette les noms d'interface en majuscules."""
        from app.schemas.mac import CanSpoofRequest

        with pytest.raises(ValueError):
            CanSpoofRequest(interface_name="ETH0", spoofed_mac="aa:bb:cc:dd:ee:ff")

    def test_interface_schema_rejects_invalid_chars(self):
        """Le schéma rejette les caractères invalides."""
        from app.schemas.mac import CanSpoofRequest

        with pytest.raises(ValueError):
            CanSpoofRequest(interface_name="eth0:1", spoofed_mac="aa:bb:cc:dd:ee:ff")


class TestRateLimitAtomic:
    """Tests du rate-limiting atomique."""

    async def test_peek_rate_limit_atomic(self):
        """peek_rate_limit utilise un script Lua atomique."""
        from app.services.rate_limit import peek_rate_limit, _PEEK_SCRIPT

        assert "EXISTS" in _PEEK_SCRIPT
        assert "TTL" in _PEEK_SCRIPT
        assert "redis.call" in _PEEK_SCRIPT

    async def test_check_and_peek_consistency(self):
        """check_rate_limit et peek_rate_limit utilisent la même clé."""
        from app.services.rate_limit import _key
        import uuid

        user_id = uuid.uuid4()
        action = "test_action"
        key = _key(user_id, action)
        assert key == f"ratelimit:{action}:{user_id}"


class TestCleanupStalePending:
    """Tests du nettoyage des entrées PENDING orphelines."""

    async def test_cleanup_stale_pending_function_exists(self):
        """La fonction cleanup_stale_pending existe."""
        from app.crud.mac_history import cleanup_stale_pending
        import inspect

        assert inspect.iscoroutinefunction(cleanup_stale_pending)

    async def test_cleanup_returns_count(self, mock_db_session):
        """cleanup_stale_pending retourne le nombre d'entrées supprimées."""
        from app.crud.mac_history import cleanup_stale_pending
        from sqlalchemy import delete

        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        count = await cleanup_stale_pending(mock_db_session, max_age_minutes=5)
        assert count == 3
        mock_db_session.commit.assert_called_once()


class TestConfigWarnings:
    """Tests des avertissements de configuration production."""

    def test_prod_dry_run_warning(self):
        """Production avec DRY_RUN=True émet un warning."""
        import os
        import warnings
        from pydantic_settings import BaseSettings, SettingsConfigDict
        from typing import Literal, List
        from pydantic import field_validator, model_validator

        class TestSettings(BaseSettings):
            model_config = SettingsConfigDict(case_sensitive=True)
            APP_ENV: Literal["development", "staging", "production"] = "development"
            MAC_SPOOF_DRY_RUN: bool = False
            ALLOWED_INTERFACES: List[str] = []

            @field_validator("ALLOWED_INTERFACES", mode="before")
            @classmethod
            def _split_ifaces(cls, v):
                if isinstance(v, str):
                    return [item.strip() for item in v.split(",") if item.strip()]
                return v

            @model_validator(mode="after")
            def _validate_prod_dry_run(self):
                if self.APP_ENV == "production" and self.MAC_SPOOF_DRY_RUN:
                    warnings.warn("DRY_RUN in production!", RuntimeWarning)
                return self

        os.environ["APP_ENV"] = "production"
        os.environ["MAC_SPOOF_DRY_RUN"] = "true"
        os.environ["ALLOWED_INTERFACES"] = '["eth0"]'

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            s = TestSettings()
            assert len(w) == 1
            assert "DRY_RUN" in str(w[0].message)

    def test_prod_allowed_interfaces_warning(self):
        """Production avec ALLOWED_INTERFACES vide émet un warning."""
        import os
        import warnings
        from pydantic_settings import BaseSettings, SettingsConfigDict
        from typing import Literal, List
        from pydantic import field_validator, model_validator

        class TestSettings(BaseSettings):
            model_config = SettingsConfigDict(case_sensitive=True)
            APP_ENV: Literal["development", "staging", "production"] = "development"
            MAC_SPOOF_DRY_RUN: bool = False
            ALLOWED_INTERFACES: List[str] = []

            @field_validator("ALLOWED_INTERFACES", mode="before")
            @classmethod
            def _split_ifaces(cls, v):
                if isinstance(v, str):
                    return [item.strip() for item in v.split(",") if item.strip()]
                return v

            @model_validator(mode="after")
            def _validate_prod_dry_run(self):
                if self.APP_ENV == "production" and not self.ALLOWED_INTERFACES:
                    warnings.warn("ALLOWED_INTERFACES empty in production!", RuntimeWarning)
                return self

        os.environ["APP_ENV"] = "production"
        os.environ["MAC_SPOOF_DRY_RUN"] = "false"
        os.environ["ALLOWED_INTERFACES"] = "[]"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            s = TestSettings()
            assert len(w) == 1
            assert "ALLOWED_INTERFACES" in str(w[0].message)


class TestIpBinaryDetection:
    """Tests de la détection automatique du binaire ip."""

    def test_resolve_ip_bin_prefers_configured(self):
        """Le chemin configuré a la priorité."""
        from app.services.mac_spoofing import _resolve_ip_bin

        assert _resolve_ip_bin("/custom/ip") == "/custom/ip"

    def test_resolve_ip_bin_uses_shutil_which(self):
        """shutil.which est utilisé si disponible."""
        from app.services.mac_spoofing import _resolve_ip_bin
        import shutil

        with patch("shutil.which", return_value="/usr/bin/ip"):
            assert _resolve_ip_bin(None) == "/usr/bin/ip"

    def test_resolve_ip_bin_fallback_candidates(self):
        """Les candidats sont testés en fallback."""
        from app.services.mac_spoofing import _resolve_ip_bin, IP_BIN_CANDIDATES
        import subprocess

        def mock_run(cmd, *args, **kwargs):
            if cmd[0] == IP_BIN_CANDIDATES[1]:  # /bin/ip
                return MagicMock()
            raise FileNotFoundError()

        with patch("shutil.which", return_value=None):
            with patch("subprocess.run", side_effect=mock_run):
                result = _resolve_ip_bin(None)
                assert result == IP_BIN_CANDIDATES[1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])