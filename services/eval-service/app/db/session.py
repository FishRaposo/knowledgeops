"""Async database session for the Eval Service with graceful fallback."""

import logging

from shared.db import create_async_engine_and_session, is_db_available

from app.config import EvalSettings

logger = logging.getLogger(__name__)

settings = EvalSettings()

engine, async_session_factory = create_async_engine_and_session(
    settings.database_url, echo=False, pool_size=10
)

db_available: bool = False


async def check_db() -> bool:
    """Probe database availability and cache the result."""
    global db_available
    db_available = await is_db_available(engine)
    if db_available:
        logger.info("Database connected for eval service.")
    else:
        logger.warning("Database unavailable — falling back to in-memory eval store.")
    return db_available


async def close_db() -> None:
    await engine.dispose()
