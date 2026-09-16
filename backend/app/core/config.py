"""
Configuration centralisée — chargée depuis les variables d'environnement.
Utilise Pydantic Settings v2 pour la validation et le typage strict.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration globale de l'application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Général ---
    APP_NAME: str = "MAC Spoofing Platform"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # --- Sécurité ---
    SECRET_KEY: str = Field(..., min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- CORS ---
    BACKEND_CORS_ORIGINS: list[str] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    # --- PostgreSQL ---
    DATABASE_URL: PostgresDsn
    DATABASE_URL_SYNC: PostgresDsn

    # --- Redis / Celery ---
    CELERY_BROKER_URL: RedisDsn
    CELERY_RESULT_BACKEND: RedisDsn

    # --- Worker MAC ---
    DEFAULT_INTERFACE: str = "eth0"
    IP_BIN: str = "/usr/sbin/ip"
    MAC_SPOOF_DRY_RUN: bool = True
    MAC_SPOOF_RATE_LIMIT_SECONDS: int = 30
    MAC_SPOOF_CMD_TIMEOUT: int = 5

    ALLOWED_INTERFACES: list[str] = []

    @field_validator("ALLOWED_INTERFACES", mode="before")
    @classmethod
    def _split_ifaces(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    # --- Frontend ---
    VITE_API_BASE_URL: str = "http://localhost:8000/api/v1"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retourne une instance unique (cache) des paramètres."""
    return Settings()  # type: ignore[call-arg]


settings = get_settings()