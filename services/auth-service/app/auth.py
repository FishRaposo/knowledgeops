"""Authentication utilities for JWT and API key validation."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

import jwt
from pydantic import BaseModel, Field

from app.config import AuthSettings

settings = AuthSettings()


class TokenPayload(BaseModel):
    """JWT token payload.

    Attributes:
        user_id: User identifier.
        email: User email.
        role: User role.
        exp: Token expiration timestamp.
        iat: Token issued-at timestamp.
    """

    user_id: str = Field(description="User identifier")
    email: str = Field(description="User email")
    role: str = Field(description="User role")
    exp: datetime = Field(description="Expiration timestamp")
    iat: datetime = Field(description="Issued-at timestamp")


class TokenResponse(BaseModel):
    """Token exchange response.

    Attributes:
        access_token: JWT access token.
        token_type: Token type (always "bearer").
        expires_in: Seconds until expiration.
    """

    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Seconds until expiration")


def hash_api_key(key: str) -> str:
    """Hash an API key using SHA-256.

    Args:
        key: Raw API key string.

    Returns:
        Hex-encoded SHA-256 hash.
    """
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a new API key with a prefixed format.

    Returns:
        A string prefixed with 'kops_' followed by a random hex string.
    """
    return f"kops_{secrets.token_hex(32)}"


def create_access_token(user_id: UUID, email: str, role: str) -> TokenResponse:
    """Create a JWT access token for a user.

    Args:
        user_id: User identifier.
        email: User email address.
        role: User RBAC role.

    Returns:
        Token response with access token and metadata.
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.jwt_expiration_minutes)

    payload = {
        "user_id": str(user_id),
        "email": email,
        "role": role,
        "exp": expires,
        "iat": now,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "jti": secrets.token_urlsafe(16),
    }

    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expiration_minutes * 60,
    )


def verify_token(token: str) -> Optional[TokenPayload]:
    """Verify and decode a JWT access token.

    Validates issuer, audience, expiration, and issued-at claims.

    Args:
        token: JWT token string.

    Returns:
        Decoded token payload, or None if invalid.
    """
    try:
        decoded: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["exp", "iat", "iss", "aud"]},
        )
        return TokenPayload(**decoded)
    except jwt.PyJWTError:
        return None


def check_permission(role: str, required_role: str) -> bool:
    """Check if a user role has sufficient permissions.

    Args:
        role: User's current role.
        required_role: Minimum required role.

    Returns:
        True if the user has sufficient permissions.
    """
    role_hierarchy = {"admin": 3, "user": 2, "viewer": 1}
    return role_hierarchy.get(role, 0) >= role_hierarchy.get(required_role, 0)
