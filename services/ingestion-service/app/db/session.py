"""Async SQLAlchemy engine and session management."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import IngestionSettings

logger = logging.getLogger(__name__)

settings = IngestionSettings()

engine = create_async_engine(settings.database_url, echo=False, pool_size=10)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

db_available: bool = False


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


async def init_db() -> None:
    global db_available
    try:
        async with engine.begin() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        db_available = True
        logger.info("Database connected for ingestion service.")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        db_available = False
        logger.warning("Database unavailable — falling back to in-memory stores: %s", exc)


async def close_db() -> None:
    await engine.dispose()
