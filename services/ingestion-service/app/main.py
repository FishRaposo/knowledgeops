"""Ingestion Service for KnowledgeOps platform.

Handles document parsing, chunking, deduplication, and embedding generation.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.readiness import readiness_payload
from shared_core.errors import BaseApplicationError, application_error_handler
from shared_core.logging import setup_logging

from app.config import IngestionSettings
from app.db.session import check_db, close_db, db_available, init_db
from app.workers.ingest_worker import router as ingest_router
from app.workers.queue import close_redis_pool

settings = IngestionSettings()
setup_logging(level=settings.LOG_LEVEL, service_name="ingestion-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_redis_pool()
    await close_db()


app = FastAPI(
    title="KnowledgeOps Ingestion Service",
    version="0.1.0",
    description="Document ingestion pipeline with multi-format parsing.",
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

app.include_router(ingest_router, tags=["ingestion"])


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service health."""
    status = "healthy" if db_available else "degraded"
    return {"status": status, "service": "ingestion-service"}


@app.get("/ready")
async def ready() -> dict[str, object]:
    """Readiness probe: re-checks the database with bounded backoff."""
    return await readiness_payload("ingestion-service", check_db)
