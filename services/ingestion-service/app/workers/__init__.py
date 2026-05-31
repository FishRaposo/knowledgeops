"""Ingestion workers for async document processing."""

from app.workers.ingest_worker import router as ingest_router

__all__ = ["ingest_router"]
