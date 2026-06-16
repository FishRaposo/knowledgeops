"""Unit tests for auth utilities: hashing, key generation, JWT, RBAC."""

from uuid import uuid4

import jwt
import pytest
from app.auth import (
    check_permission,
    create_access_token,
    generate_api_key,
    hash_api_key,
    settings,
    verify_token,
)


def test_hash_api_key_is_deterministic_sha256() -> None:
    digest = hash_api_key("secret-key")
    assert digest == hash_api_key("secret-key")
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


def test_hash_api_key_differs_per_input() -> None:
    assert hash_api_key("a") != hash_api_key("b")


def test_generate_api_key_prefix_and_uniqueness() -> None:
    key1 = generate_api_key()
    key2 = generate_api_key()
    assert key1.startswith("kops_")
    assert key1 != key2
    assert len(key1) > len("kops_")


def test_create_access_token_roundtrip() -> None:
    user_id = uuid4()
    token_resp = create_access_token(user_id, "user@example.com", "admin")
    assert token_resp.token_type == "bearer"
    assert token_resp.expires_in == settings.jwt_expiration_minutes * 60

    payload = verify_token(token_resp.access_token)
    assert payload is not None
    assert payload.user_id == str(user_id)
    assert payload.email == "user@example.com"
    assert payload.role == "admin"


def test_verify_token_rejects_garbage() -> None:
    assert verify_token("not-a-jwt") is None


def test_verify_token_rejects_wrong_secret() -> None:
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    forged = jwt.encode(
        {
            "user_id": "x",
            "email": "e@e.com",
            "role": "user",
            "exp": now + timedelta(minutes=5),
            "iat": now,
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
        },
        "wrong-secret",
        algorithm=settings.jwt_algorithm,
    )
    assert verify_token(forged) is None


def test_verify_token_rejects_wrong_audience() -> None:
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "user_id": "x",
            "email": "e@e.com",
            "role": "user",
            "exp": now + timedelta(minutes=5),
            "iat": now,
            "iss": settings.jwt_issuer,
            "aud": "some-other-audience",
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    assert verify_token(token) is None


def test_verify_token_rejects_expired() -> None:
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "user_id": "x",
            "email": "e@e.com",
            "role": "user",
            "exp": now - timedelta(minutes=5),
            "iat": now - timedelta(minutes=10),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    assert verify_token(token) is None


@pytest.mark.parametrize(
    ("role", "required", "expected"),
    [
        ("admin", "viewer", True),
        ("admin", "admin", True),
        ("user", "viewer", True),
        ("user", "admin", False),
        ("viewer", "user", False),
        ("viewer", "viewer", True),
        ("unknown-role", "viewer", False),
        ("admin", "unknown-role", True),
    ],
)
def test_check_permission_hierarchy(role: str, required: str, expected: bool) -> None:
    assert check_permission(role, required) is expected
