"""Retrieval Service for KnowledgeOps platform.

Hybrid search, reranking, citation assembly, and grounded answer generation.
"""

from fastapi import FastAPI

from app.config import RetrievalSettings
from app.search.hybrid import router as search_router
from app.citation.assembler import router as citation_router
from app.generation.answer import router as generation_router

settings = RetrievalSettings()

app = FastAPI(
    title="KnowledgeOps Retrieval Service",
    version="0.1.0",
    description="Hybrid retrieval with vector and keyword search.",
)

app.include_router(search_router, tags=["search"])
app.include_router(citation_router, tags=["citation"])
app.include_router(generation_router, tags=["generation"])


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service health."""
    return {"status": "healthy", "service": "retrieval-service"}
