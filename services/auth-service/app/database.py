"""Async database engine and session factory for the Auth Service.

Backed by shared_core.
"""

import logging
from collections.abc import AsyncGenerator

from shared_core.database import AsyncDatabaseManager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import AuthSettings

logger = logging.getLogger(__name__)

settings = AuthSettings()

_db = AsyncDatabaseManager(settings.DATABASE_URL, pool_size=5, max_overflow=10)
engine = _db.engine
async_session_factory = _db.AsyncSessionLocal


async def check_db() -> bool:
    """Probe database connectivity for the readiness endpoint.

    Returns ``True`` when a trivial ``SELECT 1`` succeeds, ``False`` otherwise.
    Never raises.
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("Auth DB probe failed: %s", exc)
        return False


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
