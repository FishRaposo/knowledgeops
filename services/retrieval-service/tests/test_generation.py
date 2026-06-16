"""Tests for refusal logic, citation assembly, and grounded generation."""

from types import SimpleNamespace
from typing import Any

import pytest
from app.citation.assembler import _chunk_to_citation
from app.generation.answer import _build_rag_prompt, _estimate_tokens, generate_answer
from app.generation.refusal import check_refusal, format_refusal
from app.search.index import index


def _result(chunk_id: str, score: float, content: str = "context") -> SimpleNamespace:
    return SimpleNamespace(
        chunk_id=chunk_id,
        document_id="d1",
        content=content,
        score=score,
        metadata={},
    )


# --- refusal -----------------------------------------------------------------


def test_check_refusal_empty_results() -> None:
    assert check_refusal([], 0.7) is True


def test_check_refusal_below_threshold() -> None:
    assert check_refusal([_result("c1", 0.5)], 0.7) is True


def test_check_refusal_above_threshold() -> None:
    assert check_refusal([_result("c1", 0.9)], 0.7) is False


def test_format_refusal_shape() -> None:
    out = format_refusal("no match")
    assert out["refusal"] is True
    assert out["refusal_reason"] == "no match"
    assert out["citations"] == []
    assert out["confidence"] == 0.0


# --- citation assembly -------------------------------------------------------


def test_chunk_to_citation_truncates_long_excerpt() -> None:
    chunk = {
        "id": "c1",
        "document_id": "d1",
        "content": "x" * 500,
        "metadata": {},
    }
    citation = _chunk_to_citation(chunk, score=0.9, doc={"id": "d1", "title": "Doc"})
    assert citation.document_title == "Doc"
    assert len(citation.excerpt) == 200
    assert citation.relevance_score == 0.9


def test_chunk_to_citation_metadata_title_fallback() -> None:
    chunk = {
        "id": "c1",
        "document_id": "unknown-doc",
        "content": "short",
        "metadata": {"title": "FromMeta"},
    }
    citation = _chunk_to_citation(chunk, doc=None)
    assert citation.document_title in {"FromMeta", "Document"}
    assert citation.excerpt == "short"


# --- prompt building ---------------------------------------------------------


def test_build_rag_prompt_includes_context_and_question() -> None:
    prompt = _build_rag_prompt("What is X?", [_result("c1", 0.9, "X is a thing")])
    assert "Context chunks:" in prompt
    assert "What is X?" in prompt
    assert "X is a thing" in prompt


def test_estimate_tokens_monotonic() -> None:
    assert _estimate_tokens("") == 1
    assert _estimate_tokens("a" * 40) == 10


# --- generate_answer ---------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_answer_no_results() -> None:
    out = await generate_answer("q", [])
    assert out["confidence"] == 0.0
    assert out["citations"] == []
    assert "could not find" in out["answer"].lower()


@pytest.mark.asyncio
async def test_generate_answer_falls_back_when_gateway_down(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the LLM gateway is unreachable, generation degrades to excerpts."""
    index.clear()
    index.store_document({"id": "d1", "title": "Doc"})
    index.store_chunk({"id": "c1", "document_id": "d1", "content": "grounded text"})

    async def _no_trace(*_a: Any, **_k: Any) -> None:
        return None

    monkeypatch.setattr("app.generation.answer._emit_cost_trace", _no_trace)

    results = [_result("c1", 0.85, "grounded text")]
    out = await generate_answer("question", results)
    assert "citations" in out
    assert out["confidence"] == pytest.approx(0.85)
    # The fallback answer includes the context excerpt.
    assert "grounded text" in out["answer"]
    index.clear()
