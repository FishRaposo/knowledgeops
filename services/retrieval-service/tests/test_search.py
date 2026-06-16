"""Unit tests for retrieval search internals: index, fusion, reranking."""

import pytest
from app.search.hybrid import (
    SearchResult,
    _reciprocal_rank_fusion,
)
from app.search.index import InMemoryIndex, _cosine_similarity, _tokenize
from app.search.reranking import RankedResult, _terms, rerank_results

# --- cosine similarity (golden-pinned) --------------------------------------


def test_cosine_similarity_identical_vectors() -> None:
    assert _cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal() -> None:
    assert _cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_similarity_mismatched_or_empty() -> None:
    assert _cosine_similarity([], [1.0]) == 0.0
    assert _cosine_similarity([1.0, 2.0], [1.0]) == 0.0
    assert _cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_cosine_similarity_golden_value() -> None:
    # Pins the exact rounded value to guard against silent numeric drift.
    score = _cosine_similarity([1.0, 2.0, 3.0], [4.0, 5.0, 6.0])
    assert round(score, 4) == 0.9746


# --- tokenization ------------------------------------------------------------


def test_tokenize_lowercases_and_splits() -> None:
    assert _tokenize("Hello World hello") == {"hello", "world"}


# --- in-memory index ---------------------------------------------------------


def test_index_store_and_keyword_search() -> None:
    idx = InMemoryIndex()
    idx.store_document({"id": "d1", "title": "Doc"})
    idx.store_chunk({"id": "c1", "document_id": "d1", "content": "the quick brown fox"})
    idx.store_chunk({"id": "c2", "document_id": "d1", "content": "lazy dog sleeps"})
    results = idx.keyword_search("quick fox", top_k=5)
    assert results
    top_chunk, score = results[0]
    assert top_chunk["id"] == "c1"
    assert score > 0


def test_index_keyword_search_empty_index() -> None:
    idx = InMemoryIndex()
    assert idx.keyword_search("anything", 5) == []


def test_index_get_helpers_and_clear() -> None:
    idx = InMemoryIndex()
    idx.store_documents([{"id": "d1", "title": "T"}])
    idx.store_chunks(
        [
            {"id": "c1", "document_id": "d1", "content": "a"},
            {"id": "c2", "document_id": "d1", "content": "b"},
        ]
    )
    assert idx.chunk_count == 2
    assert idx.get_document("d1")["title"] == "T"
    assert idx.get_chunk("c1")["content"] == "a"
    assert len(idx.get_chunks_by_ids(["c1", "c2", "missing"])) == 2
    assert len(idx.get_chunks_by_document("d1")) == 2
    idx.clear()
    assert idx.chunk_count == 0


@pytest.mark.asyncio
async def test_index_vector_search_empty() -> None:
    idx = InMemoryIndex()
    assert await idx.vector_search("q", 5) == []


# --- reciprocal rank fusion --------------------------------------------------


def test_rrf_merges_and_boosts_shared_results() -> None:
    a = SearchResult(chunk_id="c1", document_id="d", content="x", score=0.9)
    b = SearchResult(chunk_id="c2", document_id="d", content="y", score=0.8)
    vector = [a, b]
    keyword = [a]  # c1 appears in both -> ranked first
    fused = _reciprocal_rank_fusion(vector, keyword)
    assert fused[0].chunk_id == "c1"
    assert {r.chunk_id for r in fused} == {"c1", "c2"}


# --- reranking ---------------------------------------------------------------


def test_terms_drops_stopwords_and_short_tokens() -> None:
    terms = _terms("The quick brown fox and the lazy dog")
    assert "the" not in terms
    assert "and" not in terms
    assert "quick" in terms


def test_rerank_orders_by_relevance() -> None:
    results = [
        RankedResult(
            chunk_id="c1",
            document_id="d",
            content="completely unrelated content here",
            score=0.5,
        ),
        RankedResult(
            chunk_id="c2",
            document_id="d",
            content="machine learning models for retrieval",
            score=0.5,
        ),
    ]
    reranked = rerank_results(results, "machine learning retrieval", top_k=2)
    assert reranked[0].chunk_id == "c2"
    assert reranked[0].score >= reranked[1].score
    assert all(0.0 <= r.score <= 1.0 for r in reranked)


def test_rerank_phrase_bonus_and_topk() -> None:
    results = [
        RankedResult(
            chunk_id=f"c{i}",
            document_id="d",
            content="refund policy details" if i == 0 else "noise text",
            score=0.4,
        )
        for i in range(5)
    ]
    reranked = rerank_results(results, "refund policy", top_k=3)
    assert len(reranked) == 3
    assert reranked[0].chunk_id == "c0"
