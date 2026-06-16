"""Pytest fixtures for the Eval Service."""

import pytest_asyncio
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
