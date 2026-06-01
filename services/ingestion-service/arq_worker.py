"""Standalone arq worker for the ingestion service."""

import logging

from arq.connections import RedisSettings
from arq.worker import Worker

from app.config import IngestionSettings
from app.workers.ingest_worker import _process_document_background
from app.parsers.base import ParseResult

settings = IngestionSettings()
logger = logging.getLogger("arq.worker")


async def process_document(
    ctx: dict,
    *,
    job_id: str,
    doc_id: str,
    parse_result: ParseResult | dict[str, Any],
    filename: str,
    content_hash: str,
    version: int,
) -> None:
    """arq task wrapper around _process_document_background."""
    if isinstance(parse_result, dict):
        parse_result = ParseResult(**parse_result)
    await _process_document_background(
        job_id=job_id,
        doc_id=doc_id,
        parse_result=parse_result,
        filename=filename,
        content_hash=content_hash,
        version=version,
    )


class IngestionWorker(Worker):
    """Custom arq worker with our task functions."""

    functions = [process_document]


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)
    redis_settings = RedisSettings.from_url(settings.redis_url)
    worker = IngestionWorker(
        redis_settings=redis_settings,
        burst=False,
        poll_delay=1.0,
        max_jobs=10,
    )
    asyncio.run(worker.main())
