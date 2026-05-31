"""Shared pytest fixtures for integration tests."""

import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
API_GATEWAY_URL = f"{API_BASE}"


def _make_response(status_code: int, json_data: Any) -> MagicMock:
    """Create a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json = MagicMock(return_value=json_data)
    return resp


@pytest.fixture
def client() -> MagicMock:
    """Provide a mocked async HTTP client for integration testing.

    Returns a MagicMock mimicking httpx.AsyncClient with AsyncMock get/post
    that return realistic canned responses, avoiding the need for running services.
    """

    async def mock_get(url: str, **kwargs: Any) -> MagicMock:
        if "/health" in url:
            return _make_response(200, {"status": "healthy", "services": []})
        if "/api/documents" in url:
            return _make_response(200, [])
        if "/api/evals" in url:
            return _make_response(200, [])
        if "/api/traces" in url:
            return _make_response(200, [])
        if "/api/costs" in url:
            return _make_response(
                200,
                {
                    "total_usd": 0.0,
                    "by_service": {},
                    "by_model": {},
                    "total_prompt_tokens": 0,
                    "total_completion_tokens": 0,
                },
            )
        return _make_response(404, {})

    async def mock_post(url: str, **kwargs: Any) -> MagicMock:
        if "/upload" in url:
            files: dict = kwargs.get("files", {})
            for file_info in files.values():
                filename: str = file_info[0] if file_info else ""
                if filename.endswith(".exe"):
                    return _make_response(400, {"detail": "Unsupported file format"})
            return _make_response(
                200,
                {
                    "id": "test-doc-id",
                    "title": "Test Document",
                    "source": "test_doc.md",
                    "status": "processing",
                    "version": 1,
                    "chunk_count": 0,
                    "created_at": "2024-01-01T00:00:00Z",
                },
            )
        if "/query" in url:
            body: dict = kwargs.get("json", {})
            query_text: str = body.get("query", "")
            return _make_response(
                200,
                {
                    "answer": "The refund policy allows returns within 30 days of purchase.",
                    "citations": [
                        {
                            "chunk_id": "chunk-1",
                            "document_id": "doc-1",
                            "document_title": "Refund Policy",
                            "excerpt": "Returns are accepted within 30 days...",
                            "relevance_score": 0.95,
                        }
                    ],
                    "refusal": False,
                    "query": query_text,
                },
            )
        return _make_response(404, {})

    mock = MagicMock()
    mock.get = AsyncMock(side_effect=mock_get)
    mock.post = AsyncMock(side_effect=mock_post)
    return mock


@pytest.fixture
def sample_markdown_content() -> str:
    """Provide sample markdown content for upload testing.

    Returns:
        A short markdown document for testing ingestion.
    """
    return """# Test Document

This is a test document for integration testing.

## Section One

The quick brown fox jumps over the lazy dog. This content is used to verify
that the ingestion pipeline correctly parses, chunks, and stores documents.

## Section Two

Additional test content for chunking validation. Each section should be
processed independently and create appropriate chunks with overlap.
"""
