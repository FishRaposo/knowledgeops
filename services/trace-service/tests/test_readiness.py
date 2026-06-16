"""Tests for the /ready readiness probe and the shared backoff helper."""

import pytest
from httpx import AsyncClient
from shared.readiness import probe_database, readiness_payload


@pytest.mark.asyncio
async def test_ready_endpoint_reports_degraded_without_db(client: AsyncClient) -> None:
    resp = await client.get("/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ready"] is True
    assert body["service"] == "trace-service"
    # No live PostgreSQL in unit tests -> degraded mode.
    assert body["database"] == "down"
    assert body["mode"] == "degraded"


@pytest.mark.asyncio
async def test_probe_database_returns_true_on_first_success() -> None:
    calls = {"n": 0}

    async def _check() -> bool:
        calls["n"] += 1
        return True

    assert await probe_database(_check, retries=3, base_delay=0.0) is True
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_probe_database_retries_then_succeeds() -> None:
    calls = {"n": 0}

    async def _check() -> bool:
        calls["n"] += 1
        return calls["n"] >= 2

    assert await probe_database(_check, retries=3, base_delay=0.0) is True
    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_probe_database_swallows_exceptions() -> None:
    async def _check() -> bool:
        raise ConnectionError("db down")

    assert await probe_database(_check, retries=2, base_delay=0.0) is False


@pytest.mark.asyncio
async def test_readiness_payload_up_when_db_ok() -> None:
    async def _ok() -> bool:
        return True

    payload = await readiness_payload("svc", _ok, base_delay=0.0)
    assert payload == {
        "ready": True,
        "service": "svc",
        "database": "up",
        "mode": "persistent",
    }
