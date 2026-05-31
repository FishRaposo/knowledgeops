"""In-memory document/chunk index with vector and keyword search."""

import math
from typing import Any

import httpx

from app.config import RetrievalSettings

settings = RetrievalSettings()


class InMemoryIndex:

    _chunks: dict[str, dict[str, Any]]
    _documents: dict[str, dict[str, Any]]

    def __init__(self) -> None:
        self._chunks = {}
        self._documents = {}

    def store_document(self, doc: dict[str, Any]) -> None:
        self._documents[doc["id"]] = doc

    def store_chunk(self, chunk: dict[str, Any]) -> None:
        self._chunks[chunk["id"]] = chunk

    def store_chunks(self, chunks: list[dict[str, Any]]) -> None:
        for chunk in chunks:
            self._chunks[chunk["id"]] = chunk

    def store_documents(self, docs: list[dict[str, Any]]) -> None:
        for doc in docs:
            self._documents[doc["id"]] = doc

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        return self._documents.get(doc_id)

    def get_chunk(self, chunk_id: str) -> dict[str, Any] | None:
        return self._chunks.get(chunk_id)

    def get_chunks_by_ids(self, chunk_ids: list[str]) -> list[dict[str, Any]]:
        return [self._chunks[cid] for cid in chunk_ids if cid in self._chunks]

    def get_chunks_by_document(self, doc_id: str) -> list[dict[str, Any]]:
        return [c for c in self._chunks.values() if c.get("document_id") == doc_id]

    def clear(self) -> None:
        self._chunks.clear()
        self._documents.clear()

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    async def _get_query_embedding(self, query: str) -> list[float]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.llm_gateway_url}/v1/embeddings",
                json={"input": query, "model": "text-embedding-3-small"},
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return list(data["data"][0]["embedding"])

    async def vector_search(
        self, query: str, top_k: int
    ) -> list[tuple[dict[str, Any], float]]:
        results: list[tuple[dict[str, Any], float]] = []

        if not self._chunks:
            return results

        try:
            query_emb = await self._get_query_embedding(query)
        except Exception:
            return results

        for chunk in self._chunks.values():
            emb = chunk.get("embedding")
            if emb is None:
                continue
            sim = _cosine_similarity(query_emb, emb)
            results.append((chunk, sim))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def keyword_search(
        self, query: str, top_k: int
    ) -> list[tuple[dict[str, Any], float]]:
        results: list[tuple[dict[str, Any], float]] = []

        if not self._chunks:
            return results

        query_terms = _tokenize(query)

        for chunk in self._chunks.values():
            content_terms = _tokenize(chunk.get("content", ""))
            if not query_terms:
                continue
            overlap = len(query_terms & content_terms)
            if overlap > 0:
                score = overlap / len(query_terms)
                results.append((chunk, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


def _tokenize(text: str) -> set[str]:
    return set(text.lower().split())


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot_product = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


index = InMemoryIndex()
