"""Basic endpoint tests for the Retrieval Service."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "retrieval-service"
    assert data["status"] in ("healthy", "degraded")


@pytest.mark.asyncio
async def test_search_empty(client: AsyncClient) -> None:
    response = await client.post("/retrieve/search", json={"query": "test", "top_k": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "test"
    assert data["results"] == []
