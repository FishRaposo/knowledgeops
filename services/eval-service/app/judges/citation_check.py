"""Citation verification judge."""

from typing import Any


def check_citations(
    expected_citations: list[str],
    actual_citations: list[dict[str, Any]],
) -> bool:
    """Verify that expected citations are present in actual results.

    Checks that at least one expected citation source appears in the
    actual citations returned by the retrieval system.

    Args:
        expected_citations: List of expected citation identifiers or titles.
        actual_citations: Actual citations from the retrieval response.

    Returns:
        True if at least one expected citation is found.
    """
    if not expected_citations:
        return True

    if not actual_citations:
        return False

    actual_titles = {
        c.get("document_title", "").lower()
        for c in actual_citations
        if isinstance(c, dict)
    }
    actual_excerpts = {
        c.get("excerpt", "").lower()
        for c in actual_citations
        if isinstance(c, dict)
    }

    for expected in expected_citations:
        expected_lower = expected.lower()
        if any(expected_lower in title for title in actual_titles):
            return True
        if any(expected_lower in excerpt for excerpt in actual_excerpts):
            return True

    return False
