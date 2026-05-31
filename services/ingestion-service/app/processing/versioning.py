"""Document versioning for re-ingestion tracking."""




_document_versions: dict[str, int] = {}


def get_next_version(source: str) -> int:
    """Get the next version number for a document source.

    Args:
        source: Document source identifier (filename or URI).

    Returns:
        Next version number (1 for first ingestion).
    """
    current = _document_versions.get(source, 0)
    next_version = current + 1
    _document_versions[source] = next_version
    return next_version


def reset_versions() -> None:
    """Reset all version tracking. Used for testing."""
    _document_versions.clear()
