"""Retrieval Service for KnowledgeOps platform.

Hybrid search, reranking, citation assembly, and grounded answer generation.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.readiness import readiness_payload
from shared_core.errors import BaseApplicationError, application_error_handler
from shared_core.logging import setup_logging

from app.citation.assembler import router as citation_router
from app.config import RetrievalSettings
from app.db.session import check_db, close_db, db_available
from app.generation.answer import router as generation_router
from app.search.hybrid import router as search_router

settings = RetrievalSettings()
setup_logging(level=settings.LOG_LEVEL, service_name="retrieval-service")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: probe DB availability. Shutdown: dispose engine."""
    await check_db()
    yield
    await close_db()


app = FastAPI(
    title="KnowledgeOps Retrieval Service",
    version="0.1.0",
    description="Hybrid retrieval with vector and keyword search.",
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

app.include_router(search_router, tags=["search"])
app.include_router(citation_router, tags=["citation"])
app.include_router(generation_router, tags=["generation"])


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service health."""
    status = "healthy" if db_available else "degraded"
    return {"status": status, "service": "retrieval-service"}


@app.get("/ready")
async def ready() -> dict[str, object]:
    """Readiness probe: re-checks the database with bounded backoff."""
    return await readiness_payload("retrieval-service", check_db)
