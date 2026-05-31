"""Content deduplication using SHA-256 hashing."""

import hashlib


def compute_hash(content: str) -> str:
    """Compute SHA-256 hash of text content.

    Args:
        content: Text content to hash.

    Returns:
        Hex-encoded SHA-256 hash string.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


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
