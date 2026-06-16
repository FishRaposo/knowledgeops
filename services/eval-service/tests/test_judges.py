"""Unit tests for eval judges: semantic match, citation, refusal."""

import pytest
from app.judges.citation_check import check_citations
from app.judges.refusal_check import check_refusal, validate_refusal_response
from app.judges.semantic_match import (
    cosine_similarity,
    lexical_similarity,
    semantic_match_score,
)

# --- cosine similarity (golden-pinned) --------------------------------------


def test_cosine_similarity_identical() -> None:
    assert cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)


def test_cosine_similarity_mismatched_or_zero() -> None:
    assert cosine_similarity([1.0], [1.0, 2.0]) == 0.0
    assert cosine_similarity([], []) == 0.0
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_cosine_similarity_golden_value() -> None:
    # Rounds to 4 dp internally; pin the value to detect numeric drift.
    assert cosine_similarity([1.0, 2.0, 3.0], [4.0, 5.0, 6.0]) == 0.9746


# --- lexical similarity (fallback, golden-pinned) ---------------------------


def test_lexical_similarity_identical() -> None:
    assert lexical_similarity("the refund policy", "the refund policy") == 1.0


def test_lexical_similarity_disjoint() -> None:
    assert lexical_similarity("apples oranges", "cars trucks") == 0.0


def test_lexical_similarity_empty() -> None:
    assert lexical_similarity("", "anything") == 0.0


def test_lexical_similarity_partial_golden() -> None:
    # "refund" overlaps; "the"/"is" are stopwords. F1 of the overlap pinned.
    score = lexical_similarity("refund policy", "refund window")
    assert score == 0.5


# --- semantic_match_score falls back to lexical when gateway down -----------


@pytest.mark.asyncio
async def test_semantic_match_score_empty_inputs() -> None:
    assert await semantic_match_score("", "x") == 0.0
    assert await semantic_match_score("x", "") == 0.0


@pytest.mark.asyncio
async def test_semantic_match_score_lexical_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _no_embedding(_text: str) -> list[float]:
        return []

    monkeypatch.setattr("app.judges.semantic_match.get_embedding", _no_embedding)
    score = await semantic_match_score("refund policy", "refund policy")
    assert score == 1.0


# --- citation check ----------------------------------------------------------


def test_check_citations_no_expected_is_true() -> None:
    assert check_citations([], [{"document_title": "x"}]) is True


def test_check_citations_no_actual_is_false() -> None:
    assert check_citations(["policy"], []) is False


def test_check_citations_matches_title() -> None:
    actual = [{"document_title": "Refund Policy", "excerpt": "..."}]
    assert check_citations(["refund"], actual) is True


def test_check_citations_matches_excerpt() -> None:
    actual = [{"document_title": "Doc", "excerpt": "the 30 day refund window"}]
    assert check_citations(["30 day"], actual) is True


def test_check_citations_no_match() -> None:
    actual = [{"document_title": "Shipping", "excerpt": "delivery info"}]
    assert check_citations(["refund"], actual) is False


# --- refusal check -----------------------------------------------------------


@pytest.mark.parametrize(
    ("expected", "actual", "result"),
    [
        (True, True, True),
        (False, False, True),
        (True, False, False),
        (False, True, False),
    ],
)
def test_check_refusal_matrix(expected: bool, actual: bool, result: bool) -> None:
    assert check_refusal(expected, actual) is result


def test_validate_refusal_response_not_refusal() -> None:
    assert validate_refusal_response({"refusal": False})["is_valid"] is True


def test_validate_refusal_response_missing_reason() -> None:
    out = validate_refusal_response({"refusal": True, "answer": "x"})
    assert out["is_valid"] is False
    assert "reason" in out["reason"].lower()


def test_validate_refusal_response_missing_answer() -> None:
    out = validate_refusal_response({"refusal": True, "refusal_reason": "r"})
    assert out["is_valid"] is False


def test_validate_refusal_response_valid() -> None:
    out = validate_refusal_response(
        {"refusal": True, "refusal_reason": "r", "answer": "a"}
    )
    assert out["is_valid"] is True
