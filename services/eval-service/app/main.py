"""Eval Service for KnowledgeOps platform.

Runs automated RAG evaluations with semantic, citation, and refusal judges.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import EvalSettings
from app.db.session import check_db, close_db, db_available
from app.runners.rag_runner import router as runner_router
from app.reporters.markdown import router as report_router

settings = EvalSettings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: probe DB availability. Shutdown: dispose engine."""
    await check_db()
    yield
    await close_db()


app = FastAPI(
    title="KnowledgeOps Eval Service",
    version="0.1.0",
    description="RAG evaluation harness with configurable judges.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runner_router, tags=["eval"])
app.include_router(report_router, tags=["reports"])


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service health."""
    status = "healthy" if db_available else "degraded"
    return {"status": status, "service": "eval-service"}
