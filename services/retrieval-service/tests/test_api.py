"""End-to-end API tests for the retrieval service (in-memory fallback)."""

import pytest
from app.search.index import index
from httpx import AsyncClient


@pytest.fixture(autouse=True)
def _clear_index() -> None:
    index.clear()
    yield
    index.clear()


@pytest.mark.asyncio
async def test_import_and_stats(client: AsyncClient) -> None:
    payload = {
        "documents": [{"id": "d1", "title": "Doc One"}],
        "chunks": [
            {"id": "c1", "document_id": "d1", "content": "refund policy is 30 days"},
            {"id": "c2", "document_id": "d1", "content": "shipping takes a week"},
        ],
    }
    resp = await client.post("/retrieve/import", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["documents_imported"] == 1
    assert body["chunks_imported"] == 2

    stats = await client.get("/retrieve/import/stats")
    assert stats.json()["chunk_count"] == 2


@pytest.mark.asyncio
async def test_search_returns_keyword_matches(client: AsyncClient) -> None:
    await client.post(
        "/retrieve/import",
        json={
            "documents": [{"id": "d1", "title": "Doc"}],
            "chunks": [
                {
                    "id": "c1",
                    "document_id": "d1",
                    "content": "the refund policy allows returns",
                },
            ],
        },
    )
    resp = await client.post(
        "/retrieve/search", json={"query": "refund policy", "top_k": 5}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == "refund policy"
    assert any(r["chunk_id"] == "c1" for r in body["results"])


@pytest.mark.asyncio
async def test_query_refuses_without_matches(client: AsyncClient) -> None:
    resp = await client.post(
        "/retrieve/query", json={"query": "unrelated topic xyz", "top_k": 5}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["refusal"] is True
    assert body["confidence"] == 0.0
    assert body["citations"] == []


@pytest.mark.asyncio
async def test_search_validation_rejects_bad_top_k(client: AsyncClient) -> None:
    resp = await client.post("/retrieve/search", json={"query": "q", "top_k": 999})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_assemble_citations_endpoint(client: AsyncClient) -> None:
    await client.post(
        "/retrieve/import",
        json={
            "documents": [{"id": "d1", "title": "Cited Doc"}],
            "chunks": [
                {"id": "c1", "document_id": "d1", "content": "some cited content"}
            ],
        },
    )
    resp = await client.post(
        "/retrieve/citations/assemble",
        json={"chunk_ids": ["c1"], "answer": "answer text"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["document_title"] == "Cited Doc"
    assert body[0]["chunk_id"] == "c1"
