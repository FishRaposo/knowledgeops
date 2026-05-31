"""Trace Service for KnowledgeOps platform.

Distributed tracing collection, storage, query, and replay.
"""

from fastapi import FastAPI

from app.config import TraceSettings
from app.collector.trace_collector import router as collector_router
from app.storage.trace_store import router as storage_router
from app.replay.replay_engine import router as replay_router

settings = TraceSettings()

app = FastAPI(
    title="KnowledgeOps Trace Service",
    version="0.1.0",
    description="Distributed tracing collection and query.",
)

app.include_router(collector_router, tags=["collector"])
app.include_router(storage_router, tags=["storage"])
app.include_router(replay_router, tags=["replay"])


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service health."""
    return {"status": "healthy", "service": "trace-service"}
