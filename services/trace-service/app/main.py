"""Trace Service for KnowledgeOps platform.

Distributed tracing collection, storage, query, and replay.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.config import TraceSettings
from app.db.session import check_db, close_db, db_available
from app.collector.trace_collector import router as collector_router
from app.storage.trace_store import router as storage_router
from app.replay.replay_engine import router as replay_router

settings = TraceSettings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: probe DB availability. Shutdown: dispose engine."""
    await check_db()
    yield
    await close_db()


app = FastAPI(
    title="KnowledgeOps Trace Service",
    version="0.1.0",
    description="Distributed tracing collection and query.",
    lifespan=lifespan,
)

app.include_router(collector_router, tags=["collector"])
app.include_router(storage_router, tags=["storage"])
app.include_router(replay_router, tags=["replay"])


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service health."""
    status = "healthy" if db_available else "degraded"
    return {"status": status, "service": "trace-service"}
