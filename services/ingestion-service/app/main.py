"""Ingestion Service for KnowledgeOps platform.

Handles document parsing, chunking, deduplication, and embedding generation.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import IngestionSettings
from app.db.session import close_db, db_available, init_db
from app.workers.ingest_worker import router as ingest_router
from app.workers.queue import close_redis_pool

settings = IngestionSettings()


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router, tags=["ingestion"])


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service health."""
    status = "healthy" if db_available else "degraded"
    return {"status": status, "service": "ingestion-service"}
