"""Tests for the Redis-backed ingestion queue with asyncio fallback."""

from typing import Any

import pytest
from app.parsers.base import ParseResult
from app.workers import queue


@pytest.mark.asyncio
async def test_get_redis_pool_falls_back_on_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queue._redis_pool = None

    async def _boom(*_a: Any, **_k: Any) -> None:
        raise ConnectionError("no redis")

    monkeypatch.setattr(queue, "create_pool", _boom)
    pool = await queue.get_redis_pool()
    assert pool is None
    # After a failure the pool is cached as the falsy ``False`` sentinel so
    # subsequent calls short-circuit without re-attempting a connection.
    assert queue._redis_pool is False
    assert not await queue.get_redis_pool()
    queue._redis_pool = None


@pytest.mark.asyncio
async def test_enqueue_uses_asyncio_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queue._redis_pool = None

    async def _no_pool() -> None:
        return None

    called: dict[str, Any] = {}

    async def _fake_process(**kwargs: Any) -> None:
        called.update(kwargs)

    monkeypatch.setattr(queue, "get_redis_pool", _no_pool)
    monkeypatch.setattr(queue, "_process_document_background", _fake_process)

    await queue.enqueue_ingestion(
        job_id="j",
        doc_id="d",
        parse_result=ParseResult(title="T", content="c", metadata={}),
        filename="f.md",
        content_hash="h",
        version=1,
    )
    # Allow the fire-and-forget task to run.
    import asyncio

    await asyncio.sleep(0.01)
    assert called.get("job_id") == "j"
    queue._redis_pool = None


@pytest.mark.asyncio
async def test_enqueue_uses_redis_pool_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    enqueued: dict[str, Any] = {}

    class _FakePool:
        async def enqueue_job(self, name: str, **kwargs: Any) -> None:
            enqueued["name"] = name
            enqueued.update(kwargs)

    async def _pool() -> _FakePool:
        return _FakePool()

    monkeypatch.setattr(queue, "get_redis_pool", _pool)
    await queue.enqueue_ingestion(
        job_id="j2",
        doc_id="d2",
        parse_result=ParseResult(title="T", content="c", metadata={}),
        filename="f.md",
        content_hash="h",
        version=2,
    )
    assert enqueued["name"] == "process_document"
    assert enqueued["job_id"] == "j2"
