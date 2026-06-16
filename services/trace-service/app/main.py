"""Trace Service for KnowledgeOps platform.

Distributed tracing collection, storage, query, and replay.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.readiness import readiness_payload
from shared_core.errors import BaseApplicationError, application_error_handler
from shared_core.logging import setup_logging

from app.collector.trace_collector import router as collector_router
from app.config import TraceSettings
from app.db.session import check_db, close_db, db_available
from app.replay.replay_engine import router as replay_router
from app.storage.trace_store import router as storage_router

settings = TraceSettings()
setup_logging(level=settings.LOG_LEVEL, service_name="trace-service")


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

app.add_exception_handler(BaseApplicationError, application_error_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    # Bearer-token auth (no cookies); wildcard origins forbid credentials.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(collector_router, tags=["collector"])
app.include_router(storage_router, tags=["storage"])
app.include_router(replay_router, tags=["replay"])


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service health."""
    status = "healthy" if db_available else "degraded"
    return {"status": status, "service": "trace-service"}


@app.get("/ready")
async def ready() -> dict[str, object]:
    """Readiness probe: re-checks the database with bounded backoff."""
    return await readiness_payload("trace-service", check_db)
