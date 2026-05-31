"""Result reranking for improved relevance."""

import re
from typing import Any

from pydantic import BaseModel


class RankedResult(BaseModel):
    """A reranked search result.

    Attributes:
        chunk_id: Chunk identifier.
        document_id: Parent document identifier.
        content: Chunk content.
        score: Reranked relevance score.
        metadata: Additional metadata.
    """

    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: dict[str, Any] = {}


def rerank_results(
    results: list[RankedResult],
    query: str,
    top_k: int = 3,
) -> list[RankedResult]:
    """Rerank search results using a deterministic cross-encoder style scorer.

    The scorer evaluates query/document pairs together using token overlap,
    phrase matches, and source score. It is deterministic for local tests while
    preserving the cross-encoder contract that ranking is based on the pair,
    not on independent query and document embeddings only.

    Args:
        results: Fused search results to rerank.
        query: Original query for relevance computation.
        top_k: Number of top results to return.

    Returns:
        Top-k reranked results sorted by adjusted score.
    """
    query_terms = _terms(query)

    reranked: list[RankedResult] = []
    for result in results:
        content_terms = _terms(result.content)
        term_overlap = len(query_terms & content_terms) / max(len(query_terms), 1)
        phrase_bonus = 0.15 if query.lower() in result.content.lower() else 0.0
        density = len(query_terms & content_terms) / max(len(content_terms), 1)
        adjusted_score = min(1.0, 0.55 * result.score + 0.3 * term_overlap + 0.15 * density + phrase_bonus)
        reranked.append(
            RankedResult(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                content=result.content,
                score=adjusted_score,
                metadata=result.metadata,
            )
        )

    reranked.sort(key=lambda r: r.score, reverse=True)
    return reranked[:top_k]


def _terms(text: str) -> set[str]:
    stopwords = {"the", "and", "for", "with", "that", "this", "from", "about", "are", "was", "were"}
    return {
        term
        for term in re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text.lower())
        if term not in stopwords
    }
