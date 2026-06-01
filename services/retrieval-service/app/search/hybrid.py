"""Hybrid search combining vector similarity and keyword matching.

When the database is available, queries use pgvector for vector similarity
and ILIKE for keyword search.  When the database is down the service
gracefully falls back to the in-memory index.
"""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.config import RetrievalSettings
from app.db.session import async_session_factory, db_available
from app.search.index import index
from app.search.reranking import rerank_results

router = APIRouter(prefix="/retrieve")
settings = RetrievalSettings()


class ImportChunk(BaseModel):
    id: str
    document_id: str
    content: str
    chunk_index: int = 0
    embedding: list[float] | None = None
    metadata: dict[str, Any] = {}


class ImportDocument(BaseModel):
    id: str
    title: str
    source: str = ""
    status: str = "completed"
    version: int = 1
    metadata: dict[str, Any] = {}


class ImportRequest(BaseModel):
    documents: list[ImportDocument] = []
    chunks: list[ImportChunk] = []


class SearchRequest(BaseModel):
    """Search request without answer generation.

    Attributes:
        query: Search query string.
        top_k: Number of results to return.
    """

    query: str = Field(description="Search query")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results")


class SearchResult(BaseModel):
    """A single search result.

    Attributes:
        chunk_id: Chunk identifier.
        document_id: Parent document identifier.
        content: Chunk content.
        score: Relevance score (0.0-1.0).
        metadata: Additional chunk metadata.
    """

    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: dict[str, Any] = {}


class SearchResponse(BaseModel):
    """Search response with ranked results.

    Attributes:
        query: Original query string.
        results: Ranked search results.
        total: Total number of matching results.
    """

    query: str
    results: list[SearchResult]
    total: int


@router.post("/import")
async def import_data(request: ImportRequest) -> dict[str, Any]:
    """Import documents and chunks into the search backend.

    When the database is reachable the data is also persisted there so
    that subsequent searches can use pgvector.  The in-memory index is
    always updated so that a DB outage never breaks retrieval.

    Args:
        request: Import data with documents and chunks.

    Returns:
        Counts of imported items.
    """
    for doc in request.documents:
        index.store_document(doc.model_dump())
    for chunk in request.chunks:
        chunk_data = chunk.model_dump()
        chunk_data.setdefault("metadata", {})
        index.store_chunk(chunk_data)

    if db_available:
        await _persist_import_to_db(request)

    return {
        "documents_imported": len(request.documents),
        "chunks_imported": len(request.chunks),
        "total_chunks": index.chunk_count,
    }


async def _persist_import_to_db(request: ImportRequest) -> None:
    """Write imported documents and chunks to PostgreSQL."""
    async with async_session_factory() as session:
        for doc in request.documents:
            await session.execute(
                text(
                    """
                    INSERT INTO documents (id, title, source, content_hash, version, status, metadata)
                    VALUES (:id, :title, :source, :content_hash, :version, :status, :metadata)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        source = EXCLUDED.source,
                        version = EXCLUDED.version,
                        status = EXCLUDED.status,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                    """
                ),
                {
                    "id": doc.id,
                    "title": doc.title,
                    "source": doc.source,
                    "content_hash": "",
                    "version": doc.version,
                    "status": doc.status,
                    "metadata": doc.metadata,
                },
            )
        for chunk in request.chunks:
            params: dict[str, Any] = {
                "id": chunk.id,
                "document_id": chunk.document_id,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "content_hash": "",
                "metadata": chunk.metadata,
            }
            if chunk.embedding is not None:
                params["embedding"] = chunk.embedding
                await session.execute(
                    text(
                        """
                        INSERT INTO chunks (id, document_id, content, chunk_index, content_hash, embedding, metadata)
                        VALUES (:id, :document_id, :content, :chunk_index, :content_hash, :embedding, :metadata)
                        ON CONFLICT (id) DO UPDATE SET
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata
                        """
                    ),
                    params,
                )
            else:
                await session.execute(
                    text(
                        """
                        INSERT INTO chunks (id, document_id, content, chunk_index, content_hash, metadata)
                        VALUES (:id, :document_id, :content, :chunk_index, :content_hash, :metadata)
                        ON CONFLICT (id) DO UPDATE SET
                            content = EXCLUDED.content,
                            metadata = EXCLUDED.metadata
                        """
                    ),
                    params,
                )
        await session.commit()


@router.get("/import/stats")
async def import_stats() -> dict[str, Any]:
    """Get current in-memory index statistics."""
    return {
        "chunk_count": index.chunk_count,
        "document_count": len(index._documents),
        "db_available": db_available,
    }


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """Execute a hybrid search without answer generation.

    Combines vector similarity and keyword search, then reranks results.

    Args:
        request: Search request with query and top_k.

    Returns:
        Ranked search results with relevance scores.
    """
    vector_results = await _vector_search(request.query, request.top_k)
    keyword_results = await _keyword_search(request.query, request.top_k)
    fused = _reciprocal_rank_fusion(vector_results, keyword_results)
    reranked = [
        SearchResult(**result.model_dump())
        for result in rerank_results(fused, request.query, settings.rerank_top_k)
    ]

    return SearchResponse(
        query=request.query,
        results=reranked[: request.top_k],
        total=len(reranked),
    )


@router.post("/query")
async def query_with_generation(request: SearchRequest) -> dict[str, Any]:
    """Execute a full RAG query with answer generation.

    Args:
        request: Query request with search parameters.

    Returns:
        Generated answer with citations and metadata.
    """
    from app.generation.answer import generate_answer
    from app.generation.refusal import check_refusal

    search_resp = await search(request)

    if check_refusal(search_resp.results, settings.similarity_threshold):
        return {
            "answer": "I cannot answer this question based on the available documents.",
            "citations": [],
            "refusal": True,
            "refusal_reason": "No documents exceeded the similarity threshold.",
            "chunks_used": [],
            "confidence": 0.0,
            "query": request.query,
        }

    answer_data = await generate_answer(request.query, search_resp.results)

    return {
        "answer": answer_data["answer"],
        "citations": answer_data["citations"],
        "refusal": False,
        "chunks_used": [r.chunk_id for r in search_resp.results],
        "confidence": answer_data["confidence"],
        "query": request.query,
    }


async def _vector_search(query: str, top_k: int) -> list[SearchResult]:
    """Execute vector similarity search via pgvector or in-memory index."""
    if db_available:
        return await _pgvector_search(query, top_k)
    raw_results = await index.vector_search(query, top_k)
    return [
        SearchResult(
            chunk_id=chunk["id"],
            document_id=chunk["document_id"],
            content=chunk["content"],
            score=round(score, 4),
            metadata=chunk.get("metadata", {}),
        )
        for chunk, score in raw_results
    ]


async def _pgvector_search(query: str, top_k: int) -> list[SearchResult]:
    """Query pgvector for nearest chunks by cosine distance."""
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.llm_gateway_url}/v1/embeddings",
                json={"input": query, "model": "text-embedding-3-small"},
                timeout=30.0,
            )
            resp.raise_for_status()
            embedding = list(resp.json()["data"][0]["embedding"])
    except Exception:
        return []

    # pgvector <=> operator returns distance; similarity = 1 - distance
    sql = text(
        """
        SELECT id, document_id, content, chunk_index, metadata,
               1 - (embedding <=> :embedding) AS score
        FROM chunks
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> :embedding
        LIMIT :limit
        """
    )

    async with async_session_factory() as session:
        rows = await session.execute(sql, {"embedding": embedding, "limit": top_k})
        results = []
        for row in rows.mappings():
            score = row["score"]
            if score is not None and score < settings.similarity_threshold:
                continue
            results.append(
                SearchResult(
                    chunk_id=str(row["id"]),
                    document_id=str(row["document_id"]),
                    content=row["content"],
                    score=round(float(score or 0.0), 4),
                    metadata=row["metadata"] or {},
                )
            )
        return results


async def _keyword_search(query: str, top_k: int) -> list[SearchResult]:
    """Execute keyword search via PostgreSQL ILIKE or in-memory index."""
    if db_available:
        return await _pg_keyword_search(query, top_k)
    raw_results = index.keyword_search(query, top_k)
    return [
        SearchResult(
            chunk_id=chunk["id"],
            document_id=chunk["document_id"],
            content=chunk["content"],
            score=round(score, 4),
            metadata=chunk.get("metadata", {}),
        )
        for chunk, score in raw_results
    ]


async def _pg_keyword_search(query: str, top_k: int) -> list[SearchResult]:
    """Keyword search using PostgreSQL ILIKE."""
    pattern = f"%{query}%"
    sql = text(
        """
        SELECT id, document_id, content, chunk_index, metadata
        FROM chunks
        WHERE content ILIKE :pattern
        LIMIT :limit
        """
    )

    async with async_session_factory() as session:
        rows = await session.execute(sql, {"pattern": pattern, "limit": top_k})
        results = []
        for row in rows.mappings():
            results.append(
                SearchResult(
                    chunk_id=str(row["id"]),
                    document_id=str(row["document_id"]),
                    content=row["content"],
                    score=1.0,
                    metadata=row["metadata"] or {},
                )
            )
        return results


def _reciprocal_rank_fusion(
    vector_results: list[SearchResult],
    keyword_results: list[SearchResult],
    k: int = 60,
) -> list[SearchResult]:
    """Combine vector and keyword results using reciprocal rank fusion.

    Args:
        vector_results: Results from vector search.
        keyword_results: Results from keyword search.
        k: RRF constant (default 60).

    Returns:
        Fused and sorted results.
    """
    scores: dict[str, float] = {}
    results_map: dict[str, SearchResult] = {}

    for rank, result in enumerate(vector_results):
        scores[result.chunk_id] = scores.get(result.chunk_id, 0) + 1.0 / (k + rank + 1)
        results_map[result.chunk_id] = result

    for rank, result in enumerate(keyword_results):
        scores[result.chunk_id] = scores.get(result.chunk_id, 0) + 1.0 / (k + rank + 1)
        results_map[result.chunk_id] = result

    sorted_ids = sorted(scores, key=scores.get, reverse=True)
    return [results_map[cid] for cid in sorted_ids]
