"""Semantic match judge using cosine similarity via LLM Gateway embeddings."""

import math
import re
from typing import Any

import httpx

from app.config import EvalSettings

settings = EvalSettings()


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        vec_a: First embedding vector.
        vec_b: Second embedding vector.

    Returns:
        Cosine similarity between 0.0 and 1.0.
    """
    if len(vec_a) != len(vec_b) or not vec_a:
        return 0.0

    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return round(dot / (norm_a * norm_b), 4)


async def get_embedding(text: str) -> list[float]:
    """Fetch embedding vector from the LLM Gateway.

    Args:
        text: Text to embed.

    Returns:
        Embedding vector as list of floats.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.llm_gateway_url}/v1/embeddings",
            json={"input": text},
        )
        if response.status_code != 200:
            return []
        data = response.json()
        return data.get("data", [{}])[0].get("embedding", [])


async def semantic_match_score(expected: str, actual: str) -> float:
    """Compute semantic similarity using embedding vectors.

    Calls the LLM Gateway's /v1/embeddings endpoint to get embeddings
    for expected and actual text, then computes cosine similarity.

    Args:
        expected: Expected answer text.
        actual: Actual answer text.

    Returns:
        Similarity score between 0.0 and 1.0.
    """
    if not expected or not actual:
        return 0.0

    expected_embedding = await get_embedding(expected)
    actual_embedding = await get_embedding(actual)

    if not expected_embedding or not actual_embedding:
        return lexical_similarity(expected, actual)

    return cosine_similarity(expected_embedding, actual_embedding)


def lexical_similarity(expected: str, actual: str) -> float:
    """Deterministic fallback score when embeddings are unavailable."""
    expected_terms = _tokenize(expected)
    actual_terms = _tokenize(actual)
    if not expected_terms or not actual_terms:
        return 0.0
    overlap = len(expected_terms & actual_terms)
    precision = overlap / len(actual_terms)
    recall = overlap / len(expected_terms)
    if precision + recall == 0:
        return 0.0
    return round((2 * precision * recall) / (precision + recall), 4)


def _tokenize(text: str) -> set[str]:
    stopwords = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
        "in", "is", "of", "on", "or", "the", "to", "within",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token not in stopwords
    }
