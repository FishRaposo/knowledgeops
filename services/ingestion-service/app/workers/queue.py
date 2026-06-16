"""Redis-backed ingestion queue with graceful fallback to asyncio tasks."""

import asyncio
import logging
from typing import Any

from arq import create_pool
from arq.connections import RedisSettings

from app.config import IngestionSettings
from app.parsers.base import ParseResult
from app.workers.ingest_worker import _process_document_background

logger = logging.getLogger(__name__)
settings = IngestionSettings()

_redis_pool: Any = None


async def get_redis_pool() -> Any:
    """Lazy-initialise and cache the arq Redis pool."""
    global _redis_pool
    if _redis_pool is not None:
        return _redis_pool
    try:
        _redis_pool = await create_pool(
            RedisSettings.from_url(settings.REDIS_URL),
            conn_timeout=2,
            conn_retries=1,
        )
        logger.info("Redis queue connected.")
        return _redis_pool
    except Exception as exc:
        logger.warning(
            "Redis queue unavailable — falling back to asyncio tasks: %s", exc
        )
        _redis_pool = False
        return None


async def enqueue_ingestion(
    job_id: str,
    doc_id: str,
    parse_result: ParseResult,
    filename: str,
    content_hash: str,
    version: int,
) -> None:
    """Enqueue a document-processing job.

    Uses the Redis-backed arq queue when available; otherwise falls
    back to an in-process asyncio task.
    """
    pool = await get_redis_pool()
    if pool:
        await pool.enqueue_job(
            "process_document",
            job_id=job_id,
            doc_id=doc_id,
            parse_result=parse_result,
            filename=filename,
            content_hash=content_hash,
            version=version,
        )
    else:
        # TODO: Replace with Redis-based task queue for persistence.
        # Fire-and-forget asyncio.create_task loses data on restart.
        asyncio.create_task(
            _process_document_background(
                job_id=job_id,
                doc_id=doc_id,
                parse_result=parse_result,
                filename=filename,
                content_hash=content_hash,
                version=version,
            )
        )


async def close_redis_pool() -> None:
    """Close the Redis pool on shutdown."""
    global _redis_pool
    if _redis_pool and _redis_pool is not False:
        await _redis_pool.close()
    _redis_pool = None
