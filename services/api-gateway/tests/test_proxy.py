"""Tests for the API Gateway proxy router, auth dependency, and envelope helper."""

from typing import Any

import pytest
from app.main import app
from app.routes.proxy import _envelope, verify_request_auth
from fastapi import HTTPException
from httpx import AsyncClient

# --- _envelope helper --------------------------------------------------------


def test_envelope_passthrough_when_key_present() -> None:
    payload = {"documents": [1, 2]}
    assert _envelope(payload, "documents") == payload


def test_envelope_wraps_list() -> None:
    assert _envelope([1, 2], "documents") == {"documents": [1, 2]}


def test_envelope_none_collection() -> None:
    assert _envelope(None, "documents") == {"documents": []}


def test_envelope_none_scalar() -> None:
    assert _envelope(None, "document") == {"document": None}


def test_envelope_wraps_scalar_dict() -> None:
    assert _envelope({"id": "x"}, "document") == {"document": {"id": "x"}}


# --- verify_request_auth dependency -----------------------------------------


class _Req:
    def __init__(self, headers: dict[str, str]):
        self.headers = headers


@pytest.mark.asyncio
async def test_verify_request_auth_missing_header() -> None:
    with pytest.raises(HTTPException) as exc:
        await verify_request_auth(_Req({}))  # type: ignore[arg-type]
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_verify_request_auth_dev_token(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.routes import proxy

    monkeypatch.setattr(proxy.settings, "allow_dev_auth", True)
    monkeypatch.setattr(proxy.settings, "demo_token", "dev-admin-token")
    result = await verify_request_auth(
        _Req({"Authorization": "Bearer dev-admin-token"})  # type: ignore[arg-type]
    )
    assert result["role"] == "admin"
    assert result["user_id"] == "dev-admin"


# --- proxy endpoints via dependency override (dev auth) ---------------------


def _override_admin() -> dict[str, Any]:
    return {
        "valid": True,
        "user_id": "dev-admin",
        "email": "admin@knowledgeops.local",
        "role": "admin",
    }


def _override_viewer() -> dict[str, Any]:
    return {"valid": True, "user_id": "u1", "email": "u@e.com", "role": "viewer"}


@pytest.fixture
def admin_client() -> AsyncClient:
    app.dependency_overrides[verify_request_auth] = _override_admin
    yield
    app.dependency_overrides.pop(verify_request_auth, None)


@pytest.mark.asyncio
async def test_admin_users_dev_mode(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, admin_client: None
) -> None:
    from app.routes import proxy

    monkeypatch.setattr(proxy.settings, "allow_dev_auth", True)
    resp = await client.get("/api/admin/users")
    assert resp.status_code == 200
    assert resp.json()["users"][0]["role"] == "admin"


@pytest.mark.asyncio
async def test_admin_users_requires_admin_role(client: AsyncClient) -> None:
    app.dependency_overrides[verify_request_auth] = _override_viewer
    try:
        resp = await client.get("/api/admin/users")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(verify_request_auth, None)


@pytest.mark.asyncio
async def test_admin_create_key_dev_mode(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, admin_client: None
) -> None:
    from app.routes import proxy

    monkeypatch.setattr(proxy.settings, "allow_dev_auth", True)
    resp = await client.post("/api/admin/keys", json={"name": "My Key"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "My Key"
    assert body["key"] == "ko_dev_mock_key"


@pytest.mark.asyncio
async def test_admin_health_aggregates(client: AsyncClient, admin_client: None) -> None:
    resp = await client.get("/api/admin/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body
    assert "services" in body


@pytest.mark.asyncio
async def test_query_proxy_forwards(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, admin_client: None
) -> None:
    """A query proxies to retrieval-service; httpx is mocked to a canned answer."""
    from app.routes import proxy

    class _Resp:
        status_code = 200

        def json(self) -> dict[str, Any]:
            return {"answer": "hi", "citations": [], "refusal": False}

    class _MockClient:
        def __init__(self, *a: Any, **k: Any) -> None: ...
        async def __aenter__(self) -> "_MockClient":
            return self

        async def __aexit__(self, *a: Any) -> None: ...
        async def post(self, *a: Any, **k: Any) -> _Resp:
            return _Resp()

    monkeypatch.setattr(proxy, "AsyncClient", _MockClient)
    resp = await client.post("/api/query", json={"query": "q", "top_k": 5})
    assert resp.status_code == 200
    assert resp.json()["answer"] == "hi"


@pytest.mark.asyncio
async def test_list_documents_proxy_error_propagates(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, admin_client: None
) -> None:
    from app.routes import proxy

    class _Resp:
        status_code = 503
        text = "down"

        def json(self) -> dict[str, Any]:
            return {}

    class _MockClient:
        def __init__(self, *a: Any, **k: Any) -> None: ...
        async def __aenter__(self) -> "_MockClient":
            return self

        async def __aexit__(self, *a: Any) -> None: ...
        async def get(self, *a: Any, **k: Any) -> _Resp:
            return _Resp()

    monkeypatch.setattr(proxy, "AsyncClient", _MockClient)
    resp = await client.get("/api/documents")
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_unauthenticated_query_rejected(client: AsyncClient) -> None:
    """Without dependency override, missing Authorization is a 401."""
    resp = await client.post("/api/query", json={"query": "q"})
    assert resp.status_code == 401
