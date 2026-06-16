"""Refusal detection for out-of-scope queries."""

from typing import Any


def check_refusal(results: list[Any], similarity_threshold: float = 0.7) -> bool:
    """Determine if the system should refuse to answer.

    If no search results exceed the similarity threshold, the system should
    refuse to answer rather than hallucinate.

    Args:
        results: Search results with relevance scores.
        similarity_threshold: Minimum score for a valid result.

    Returns:
        True if the system should refuse to answer.
    """
    if not results:
        return True

    max_score = max(r.score for r in results) if results else 0.0
    return max_score < similarity_threshold


def format_refusal(reason: str) -> dict[str, Any]:
    """Format a refusal response.

    Args:
        reason: Explanation for the refusal.

    Returns:
        Structured refusal response.
    """
    return {
        "answer": (
            "I cannot answer this question based on the available "
            "documents in the knowledge base."
        ),
        "citations": [],
        "refusal": True,
        "refusal_reason": reason,
        "chunks_used": [],
        "confidence": 0.0,
    }
