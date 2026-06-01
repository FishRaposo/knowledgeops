"""Shared async database utilities with availability probing."""

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = logging.getLogger(__name__)


def create_async_engine_and_session(url: str, **kwargs: Any) -> tuple[Any, async_sessionmaker[Any]]:
    """Create an async engine and session factory from a database URL.

    Args:
        url: SQLAlchemy database URL.
        **kwargs: Additional arguments passed to create_async_engine.

    Returns:
        Tuple of (engine, session_factory).
    """
    engine = create_async_engine(url, **kwargs)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return engine, session_factory


async def is_db_available(engine: Any) -> bool:
    """Probe whether the database engine is reachable.

    Args:
        engine: SQLAlchemy async engine.

    Returns:
        True if a simple SELECT 1 succeeds.
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("Database probe failed: %s", exc)
        return False
