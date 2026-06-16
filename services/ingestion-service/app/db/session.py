"""Async SQLAlchemy engine and session management (shared_core-backed)."""

import logging

from shared_core.database import AsyncDatabaseManager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import IngestionSettings

logger = logging.getLogger(__name__)

settings = IngestionSettings()

_db = AsyncDatabaseManager(settings.DATABASE_URL, pool_size=10)
engine = _db.engine
async_session_factory = _db.AsyncSessionLocal

db_available: bool = False


class Base(DeclarativeBase):
    """Service-local declarative base for ingestion ORM models."""


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


async def init_db() -> None:
    global db_available
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_available = True
        logger.info("Database connected for ingestion service.")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        db_available = False
        logger.warning(
            "Database unavailable — falling back to in-memory stores: %s", exc
        )


async def check_db() -> bool:
    """Re-probe database availability and cache the result.

    Unlike :func:`init_db`, this does not run schema creation; it is the
    cheap connectivity check used by the readiness probe.
    """
    global db_available
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_available = True
    except Exception as exc:
        db_available = False
        logger.warning("Database re-probe failed: %s", exc)
    return db_available


async def close_db() -> None:
    await _db.close()
