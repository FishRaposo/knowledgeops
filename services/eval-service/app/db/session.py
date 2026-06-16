"""Async database session for the Eval Service (shared_core-backed)."""

import logging

from app.config import EvalSettings
from shared_core.database import AsyncDatabaseManager
from sqlalchemy import text

logger = logging.getLogger(__name__)

settings = EvalSettings()

_db = AsyncDatabaseManager(settings.DATABASE_URL, pool_size=10)
engine = _db.engine
async_session_factory = _db.AsyncSessionLocal

db_available: bool = False


async def check_db() -> bool:
    """Probe database availability and cache the result."""
    global db_available
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_available = True
        logger.info("Database connected for eval service.")
    except Exception as exc:
        db_available = False
        logger.warning(
            "Database unavailable — falling back to in-memory eval store: %s", exc
        )
    return db_available


async def close_db() -> None:
    await _db.close()
