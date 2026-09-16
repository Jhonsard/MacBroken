"""
Primitives de sécurité : hash de mot de passe, JWT access/refresh.
Aucune dépendance FastAPI ici — module testable unitairement.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# ------------------------------------------------------------------
# Mot de passe — bcrypt direct
# ------------------------------------------------------------------
# bcrypt tronque à 72 octets : on refuse au-delà côté schéma Pydantic.
BCRYPT_MAX_BYTES = 72


def hash_password(plain: str) -> str:
    """Hash un mot de passe en clair avec bcrypt (cost par défaut = 12)."""
    pwd_bytes = plain.encode("utf-8")
    if len(pwd_bytes) > BCRYPT_MAX_BYTES:
        raise ValueError(
            f"Mot de passe trop long ({len(pwd_bytes)} octets, max {BCRYPT_MAX_BYTES})."
        )
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Vérifie un mot de passe contre son hash bcrypt (constant-time)."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ------------------------------------------------------------------
# JWT — access token + refresh token
# ------------------------------------------------------------------
TokenType = Literal["access", "refresh"]


def _create_token(
    subject: str | uuid.UUID,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Fabrication interne d'un JWT signé HS256."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": str(uuid.uuid4()),           # identifiant unique du token (revocation)
        "iss": settings.APP_NAME,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(
    subject: str | uuid.UUID,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Génère un access token (courte durée)."""
    return _create_token(
        subject,
        "access",
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims,
    )


def create_refresh_token(subject: str | uuid.UUID) -> str:
    """Génère un refresh token (longue durée)."""
    return _create_token(
        subject,
        "refresh",
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


class TokenError(Exception):
    """Erreur générique lors du décodage / de la validation d'un JWT."""


def decode_token(token: str, expected_type: TokenType | None = None) -> dict[str, Any]:
    """
    Décode et valide un JWT.

    Lève TokenError si :
      - signature invalide
      - token expiré
      - `expected_type` fourni et ne correspond pas au champ `type`
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM],
        )
    except JWTError as exc:
        raise TokenError(f"JWT invalide : {exc}") from exc

    if expected_type is not None and payload.get("type") != expected_type:
        raise TokenError(
            f"Type de token inattendu (attendu={expected_type}, "
            f"reçu={payload.get('type')!r})."
        )
    if "sub" not in payload:
        raise TokenError("JWT sans claim 'sub'.")

    return payload