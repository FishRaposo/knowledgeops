"""Tests for the ingestion worker API and background processing (in-memory)."""

from typing import Any

import pytest
from app.parsers.base import ParseResult
from app.workers import ingest_worker
from httpx import AsyncClient


@pytest.fixture(autouse=True)
def _clear_stores() -> None:
    ingest_worker._documents_store.clear()
    ingest_worker._chunks_store.clear()
    ingest_worker._jobs_store.clear()
    yield
    ingest_worker._documents_store.clear()
    ingest_worker._chunks_store.clear()
    ingest_worker._jobs_store.clear()


# --- upload endpoint ---------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_rejects_unsupported_format(client: AsyncClient) -> None:
    resp = await client.post(
        "/ingest/upload",
        files={"file": ("bad.xyz", b"data", "application/octet-stream")},
    )
    assert resp.status_code == 400
    assert "Unsupported file format" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_upload_markdown_enqueues(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    async def _fake_enqueue(**kwargs: Any) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(
        "app.workers.queue.enqueue_ingestion", _fake_enqueue, raising=True
    )
    resp = await client.post(
        "/ingest/upload",
        files={"file": ("notes.md", b"# Title\n\nBody text.", "text/markdown")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Title"
    assert body["status"] == "processing"
    assert body["version"] == 1
    assert captured["filename"] == "notes.md"


# --- job status endpoint -----------------------------------------------------


@pytest.mark.asyncio
async def test_get_job_status_not_found(client: AsyncClient) -> None:
    resp = await client.get("/ingest/jobs/missing")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_job_status_found(client: AsyncClient) -> None:
    ingest_worker._jobs_store["job1"] = {
        "job_id": "job1",
        "document_id": "doc1",
        "status": "processing",
        "progress": 42,
    }
    resp = await client.get("/ingest/jobs/job1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["progress"] == 42
    assert body["status"] == "processing"


# --- document CRUD in fallback (in-memory) mode -----------------------------


@pytest.mark.asyncio
async def test_get_document_not_found(client: AsyncClient) -> None:
    resp = await client.get("/ingest/documents/nope")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_and_get_and_delete_document(client: AsyncClient) -> None:
    ingest_worker._documents_store["d1"] = {
        "id": "d1",
        "title": "Doc One",
        "source": "one.md",
        "status": "completed",
        "version": 1,
        "created_at": "2026-01-01T00:00:00Z",
    }
    ingest_worker._chunks_store["d1"] = [{"id": "c1"}]

    listed = await client.get("/ingest/documents")
    assert listed.status_code == 200
    body = listed.json()
    assert body[0]["id"] == "d1"
    assert body[0]["chunk_count"] == 1

    got = await client.get("/ingest/documents/d1")
    assert got.status_code == 200
    assert got.json()["title"] == "Doc One"

    deleted = await client.delete("/ingest/documents/d1")
    assert deleted.status_code == 200
    assert "d1" not in ingest_worker._documents_store


# --- background processing function -----------------------------------------


@pytest.mark.asyncio
async def test_process_document_background_in_memory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _no_embedding(_text: str) -> None:
        return None

    monkeypatch.setattr(ingest_worker, "_generate_embedding", _no_embedding)
    monkeypatch.setattr(ingest_worker, "db_available", False)

    parse_result = ParseResult(
        title="T", content="sentence one. sentence two. sentence three.", metadata={}
    )
    await ingest_worker._process_document_background(
        job_id="jobX",
        doc_id="docX",
        parse_result=parse_result,
        filename="f.md",
        content_hash="hash",
        version=1,
    )
    job = ingest_worker._jobs_store["jobX"]
    assert job["status"] == "completed"
    assert job["progress"] == 100
    assert "docX" in ingest_worker._documents_store
    assert ingest_worker._chunks_store["docX"]


@pytest.mark.asyncio
async def test_process_document_background_records_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _boom(*_a: Any, **_k: Any) -> None:
        raise RuntimeError("chunking failed")

    monkeypatch.setattr(ingest_worker, "chunk_text", _boom)
    parse_result = ParseResult(title="T", content="text", metadata={})
    await ingest_worker._process_document_background(
        job_id="jobF",
        doc_id="docF",
        parse_result=parse_result,
        filename="f.md",
        content_hash="hash",
        version=1,
    )
    job = ingest_worker._jobs_store["jobF"]
    assert job["status"] == "failed"
    assert "chunking failed" in job["error"]
