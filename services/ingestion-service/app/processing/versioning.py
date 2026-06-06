"""Document versioning for re-ingestion tracking."""

from sqlalchemy import text

from app.db.session import async_session_factory, db_available

_document_versions: dict[str, int] = {}


async def get_next_version(source: str) -> int:
    """Get the next version number for a document source.

    Queries the documents table when the database is available, otherwise
    falls back to the in-memory tracker.

    Args:
        source: Document source identifier (filename or URI).

    Returns:
        Next version number (1 for first ingestion).
    """
    if db_available:
        async with async_session_factory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT COALESCE(MAX(v.version_number), 0) AS max_version
                    FROM document_versions v
                    JOIN documents d ON v.document_id = d.id
                    WHERE d.source = :source
                    """
                ),
                {"source": source},
            )
            row = result.mappings().one_or_none()
            current = row["max_version"] if row else 0
            return int(current) + 1

    current = _document_versions.get(source, 0)
    next_version = current + 1
    _document_versions[source] = next_version
    return next_version


def reset_versions() -> None:
    """Reset all version tracking. Used for testing."""
    _document_versions.clear()
