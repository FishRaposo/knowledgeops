"""End-to-end integration tests for the KnowledgeOps platform.

Tests cover health checks, document upload and retrieval, query with citations,
evaluation runs, and trace collection across all services.
"""

import os

import httpx
import pytest

API_BASE = os.getenv("API_BASE", "http://localhost:8000")


class TestHealthChecks:
    """Verify all services are reachable and healthy."""

    @pytest.mark.asyncio
    async def test_api_gateway_health(self, client: httpx.AsyncClient) -> None:
        """Test that the API Gateway health endpoint returns 200."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded")

    @pytest.mark.asyncio
    async def test_individual_service_health(self) -> None:
        """Test that each backend service reports healthy."""
        services = {
            "auth": f"{API_BASE.replace(':8000', ':8001')}/health",
            "ingestion": f"{API_BASE.replace(':8000', ':8002')}/health",
            "retrieval": f"{API_BASE.replace(':8000', ':8003')}/health",
            "llm-gateway": f"{API_BASE.replace(':8000', ':8004')}/health",
            "eval": f"{API_BASE.replace(':8000', ':8005')}/health",
            "trace": f"{API_BASE.replace(':8000', ':8006')}/health",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            for name, url in services.items():
                try:
                    response = await client.get(url)
                    assert response.status_code == 200, (
                        f"{name} returned {response.status_code}"
                    )
                    data = response.json()
                    assert data.get("status") == "healthy", (
                        f"{name} status: {data.get('status')}"
                    )
                except httpx.ConnectError:
                    pytest.skip(f"Service {name} not reachable")


class TestDocumentIngestion:
    """Test document upload and retrieval through the ingestion pipeline."""

    @pytest.mark.asyncio
    async def test_upload_markdown_document(self, client: httpx.AsyncClient) -> None:
        """Test uploading a Markdown document through the gateway."""
        files = {
            "file": (
                "test_doc.md",
                b"# Test Document\n\nContent for integration testing.",
                "text/markdown",
            )
        }
        response = await client.post("/api/documents/upload", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] in ("pending", "processing", "completed")
        assert data["title"] == "Test Document"

    @pytest.mark.asyncio
    async def test_list_documents(self, client: httpx.AsyncClient) -> None:
        """Test listing documents through the gateway."""
        response = await client.get("/api/documents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_upload_rejects_unsupported_format(
        self, client: httpx.AsyncClient
    ) -> None:
        """Test that unsupported file formats are rejected."""
        files = {"file": ("test.exe", b"binary content", "application/octet-stream")}
        response = await client.post("/api/documents/upload", files=files)
        assert response.status_code == 400


class TestQueryAndRetrieval:
    """Test the query and retrieval pipeline."""

    @pytest.mark.asyncio
    async def test_query_returns_response(self, client: httpx.AsyncClient) -> None:
        """Test that a query returns a structured response."""
        response = await client.post(
            "/api/query", json={"query": "What is the refund policy?", "top_k": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "citations" in data
        assert "refusal" in data
        assert "query" in data
        assert data["query"] == "What is the refund policy?"

    @pytest.mark.asyncio
    async def test_query_refusal_on_empty_kb(self, client: httpx.AsyncClient) -> None:
        """Test that queries produce valid refusal when no documents are indexed."""
        response = await client.post(
            "/api/query", json={"query": "obscure topic xyz123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data.get("refusal"), bool)


class TestEvaluation:
    """Test the evaluation pipeline."""

    @pytest.mark.asyncio
    async def test_list_eval_runs(self, client: httpx.AsyncClient) -> None:
        """Test listing evaluation runs."""
        response = await client.get("/api/evals")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestTraceCollection:
    """Test trace collection and querying."""

    @pytest.mark.asyncio
    async def test_list_traces(self, client: httpx.AsyncClient) -> None:
        """Test listing traces through the gateway."""
        response = await client.get("/api/traces")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_cost_endpoint(self, client: httpx.AsyncClient) -> None:
        """Test the cost summary endpoint."""
        response = await client.get("/api/costs")
        assert response.status_code == 200
