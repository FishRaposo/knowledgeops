"""Content deduplication using SHA-256 hashing.

The hashing primitive is delegated to ``shared_core.docparse`` so every service
in the portfolio computes content hashes identically. This swap is byte-for-byte
compatible with the previous local implementation (see
``tests/test_convergence.py``), so persisted content hashes are unchanged.
"""

from shared_core.docparse import compute_hash as _sc_compute_hash


def compute_hash(content: str) -> str:
    """Compute the SHA-256 hex digest of text content.

    Delegates to :func:`shared_core.docparse.compute_hash`, which produces an
    identical digest to the previous local ``hashlib`` implementation.

    Args:
        content: Text content to hash.

    Returns:
        Hex-encoded SHA-256 hash string.
    """
    return _sc_compute_hash(content)


def is_duplicate(content: str, existing_hashes: set[str]) -> bool:
    """Check if content matches any existing hash.

    Args:
        content: Text content to check.
        existing_hashes: Set of known content hashes.

    Returns:
        True if the content hash exists in the set.
    """
    return compute_hash(content) in existing_hashes


def filter_duplicates(contents: list[str], existing_hashes: set[str]) -> list[str]:
    """Remove duplicate content from a list.

    Args:
        contents: List of text content to deduplicate.
        existing_hashes: Set of known content hashes.

    Returns:
        Filtered list with duplicates removed.
    """
    seen: set[str] = set()
    result: list[str] = []
    for content in contents:
        h = compute_hash(content)
        if h not in existing_hashes and h not in seen:
            seen.add(h)
            result.append(content)
    return result
