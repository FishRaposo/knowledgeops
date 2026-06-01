"""Retrieval Service for KnowledgeOps platform.

Hybrid search, reranking, citation assembly, and grounded answer generation.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.config import RetrievalSettings
from app.db.session import check_db, close_db, db_available
from app.search.hybrid import router as search_router
from app.citation.assembler import router as citation_router
from app.generation.answer import router as generation_router

settings = RetrievalSettings()


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

app.include_router(search_router, tags=["search"])
app.include_router(citation_router, tags=["citation"])
app.include_router(generation_router, tags=["generation"])


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service health."""
    status = "healthy" if db_available else "degraded"
    return {"status": status, "service": "retrieval-service"}
