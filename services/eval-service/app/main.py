"""Eval Service for KnowledgeOps platform.

Runs automated RAG evaluations with semantic, citation, and refusal judges.
"""

from fastapi import FastAPI

from app.config import EvalSettings
from app.runners.rag_runner import router as runner_router
from app.reporters.markdown import router as report_router

settings = EvalSettings()

app = FastAPI(
    title="KnowledgeOps Eval Service",
    version="0.1.0",
    description="RAG evaluation harness with configurable judges.",
)

app.include_router(runner_router, tags=["eval"])
app.include_router(report_router, tags=["reports"])


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service health."""
    return {"status": "healthy", "service": "eval-service"}
