"""Basic endpoint tests for the Ingestion Service."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "ingestion-service"
    assert data["status"] in ("healthy", "degraded")


@pytest.mark.asyncio
async def test_list_documents_empty(client: AsyncClient) -> None:
    response = await client.get("/ingest/documents")
    assert response.status_code == 200
    assert response.json() == []
