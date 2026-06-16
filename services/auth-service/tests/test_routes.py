"""Integration tests for auth-service routes using ASGI transport.

DB-touching endpoints are exercised via a FakeSession dependency override so
no live PostgreSQL is required.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from app.auth import create_access_token
from app.database import get_db
from app.main import app
from app.models import ApiKeyModel, UserModel
from httpx import AsyncClient


def _admin_header() -> dict[str, str]:
    token = create_access_token(uuid4(), "admin@example.com", "admin").access_token
    return {"Authorization": f"Bearer {token}"}


def _user_header() -> dict[str, str]:
    token = create_access_token(uuid4(), "user@example.com", "user").access_token
    return {"Authorization": f"Bearer {token}"}


# --- /me and /verify (no DB) -------------------------------------------------


@pytest.mark.asyncio
async def test_me_requires_bearer(client: AsyncClient) -> None:
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_user(client: AsyncClient) -> None:
    resp = await client.get("/auth/me", headers=_admin_header())
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "admin@example.com"
    assert body["role"] == "admin"


@pytest.mark.asyncio
async def test_me_rejects_invalid_token(client: AsyncClient) -> None:
    resp = await client.get("/auth/me", headers={"Authorization": "Bearer nope"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_verify_valid_and_invalid(client: AsyncClient) -> None:
    ok = await client.get("/auth/verify", headers=_admin_header())
    assert ok.status_code == 200
    assert ok.json()["valid"] is True

    bad = await client.get("/auth/verify", headers={"Authorization": "Bearer x"})
    assert bad.status_code == 401

    missing = await client.get("/auth/verify")
    assert missing.status_code == 401


# --- /rbac/check (no DB) -----------------------------------------------------


@pytest.mark.asyncio
async def test_rbac_check_allows_and_denies(client: AsyncClient) -> None:
    allowed = await client.get(
        "/auth/rbac/check", params={"role": "admin", "required_role": "viewer"}
    )
    assert allowed.json()["allowed"] is True

    denied = await client.get(
        "/auth/rbac/check", params={"role": "viewer", "required_role": "admin"}
    )
    assert denied.json()["allowed"] is False


# --- DB-backed endpoints with a fake session --------------------------------


class _FakeResult:
    def __init__(self, scalar=None, scalars_all=None):
        self._scalar = scalar
        self._scalars_all = scalars_all or []

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        outer = self

        class _S:
            def all(self_inner):
                return outer._scalars_all

        return _S()


class FakeSession:
    """Minimal AsyncSession stand-in for route tests."""

    def __init__(self, *, user=None, api_key=None, users=None, keys=None):
        self.user = user
        self.api_key = api_key
        self.users = users or []
        self.keys = keys or []
        self.added: list = []
        self.committed = False

    async def execute(self, statement, *args, **kwargs):
        sql = str(statement).lower()
        if "from api_keys" in sql or 'from "api_keys"' in sql:
            if "count" in sql:
                return _FakeResult()
            if self.keys:
                return _FakeResult(scalars_all=self.keys)
            return _FakeResult(scalar=self.api_key)
        if "from users" in sql or 'from "users"' in sql:
            if self.users:
                return _FakeResult(scalars_all=self.users)
            return _FakeResult(scalar=self.user)
        return _FakeResult()

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        # Assign an id to freshly added objects, as the DB default would.
        for obj in self.added:
            if getattr(obj, "id", None) is None:
                obj.id = uuid4()

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        if getattr(obj, "created_at", None) is None:
            obj.created_at = datetime.now(timezone.utc)
        if getattr(obj, "id", None) is None:
            obj.id = uuid4()


def _override_db(session: FakeSession):
    async def _dep():
        yield session

    return _dep


@pytest.mark.asyncio
async def test_exchange_token_invalid_key(client: AsyncClient) -> None:
    app.dependency_overrides[get_db] = _override_db(FakeSession(api_key=None))
    try:
        resp = await client.post("/auth/token", json={"api_key": "whatever"})
        assert resp.status_code == 401
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_exchange_token_success(client: AsyncClient) -> None:
    uid = str(uuid4())
    user = UserModel(id=uid, email="u@e.com", name="U", role="user")
    api_key = ApiKeyModel(id=uuid4(), user_id=uid, key_hash="h", name="k")
    session = FakeSession(user=user, api_key=api_key)
    app.dependency_overrides[get_db] = _override_db(session)
    try:
        resp = await client.post("/auth/token", json={"api_key": "rawkey"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["token_type"] == "bearer"
        assert "access_token" in body
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_create_api_key_requires_admin(client: AsyncClient) -> None:
    app.dependency_overrides[get_db] = _override_db(FakeSession())
    try:
        resp = await client.post(
            "/auth/keys", json={"name": "k"}, headers=_user_header()
        )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_create_api_key_success_creates_user(client: AsyncClient) -> None:
    session = FakeSession(user=None)
    app.dependency_overrides[get_db] = _override_db(session)
    try:
        resp = await client.post(
            "/auth/keys",
            json={"name": "ci-key", "user_email": "new@e.com", "role": "user"},
            headers=_admin_header(),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "ci-key"
        assert body["key"].startswith("kops_")
        assert session.committed is True
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_list_users_requires_admin(client: AsyncClient) -> None:
    app.dependency_overrides[get_db] = _override_db(FakeSession())
    try:
        resp = await client.get("/auth/users", headers=_user_header())
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_list_users_returns_users(client: AsyncClient) -> None:
    users = [UserModel(id=uuid4(), email="a@e.com", name="A", role="admin")]
    app.dependency_overrides[get_db] = _override_db(FakeSession(users=users))
    try:
        resp = await client.get("/auth/users", headers=_admin_header())
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["email"] == "a@e.com"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_list_api_keys_masked(client: AsyncClient) -> None:
    keys = [ApiKeyModel(id=uuid4(), user_id=uuid4(), key_hash="abcdef1234", name="k1")]
    app.dependency_overrides[get_db] = _override_db(FakeSession(keys=keys))
    try:
        resp = await client.get("/auth/keys", headers=_admin_header())
        assert resp.status_code == 200
        body = resp.json()
        assert body[0]["key_prefix"] == "abcdef12"
        assert "key_hash" not in body[0]
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_list_api_keys_requires_auth(client: AsyncClient) -> None:
    app.dependency_overrides[get_db] = _override_db(FakeSession())
    try:
        # No bearer token -> rejected before any DB access.
        unauth = await client.get("/auth/keys")
        assert unauth.status_code == 401
        # Non-admin token -> forbidden.
        forbidden = await client.get("/auth/keys", headers=_user_header())
        assert forbidden.status_code == 403
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_revoke_api_key_requires_auth(client: AsyncClient) -> None:
    session = FakeSession()
    app.dependency_overrides[get_db] = _override_db(session)
    try:
        key_id = str(uuid4())
        # No bearer token -> rejected and nothing committed/deleted.
        unauth = await client.delete(f"/auth/keys/{key_id}")
        assert unauth.status_code == 401
        # Non-admin token -> forbidden.
        forbidden = await client.delete(f"/auth/keys/{key_id}", headers=_user_header())
        assert forbidden.status_code == 403
        assert session.committed is False
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_revoke_api_key_admin_succeeds(client: AsyncClient) -> None:
    session = FakeSession()
    app.dependency_overrides[get_db] = _override_db(session)
    try:
        resp = await client.delete(f"/auth/keys/{uuid4()}", headers=_admin_header())
        assert resp.status_code == 200
        assert session.committed is True
    finally:
        app.dependency_overrides.pop(get_db, None)
