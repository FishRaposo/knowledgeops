"""Grounded answer generation using retrieved context."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter
from shared_core.pricing import calculate_cost

from app.citation.assembler import _chunk_to_citation
from app.config import RetrievalSettings
from app.search.index import index

router = APIRouter()
settings = RetrievalSettings()

_RAG_SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions based solely on the "
    "provided context chunks. Use the context to answer the user's question. "
    "If the context does not contain the answer, say so clearly. "
    "When citing information, reference the chunk and document identifiers "
    "provided in the context markers. Be concise and accurate."
)


def _build_rag_prompt(query: str, results: list[Any]) -> str:
    parts: list[str] = ["Context chunks:"]
    for i, r in enumerate(results):
        parts.append(
            f"[Chunk {i + 1}] document_id={r.document_id} chunk_id={r.chunk_id}\n"
            f"{r.content}"
        )
    parts.append(f"\nQuestion: {query}")
    parts.append(
        "\nAnswer the question using only the context above. "
        "Include [Chunk N] references where applicable."
    )
    return "\n\n".join(parts)


async def generate_answer(query: str, results: list[Any]) -> dict[str, Any]:
    """Generate a grounded answer from retrieved chunks via the LLM Gateway.

    Args:
        query: User's natural language question.
        results: Retrieved search results for context.

    Returns:
        Dictionary with answer text, citations, and confidence.
    """
    if not results:
        return {
            "answer": (
                "I could not find any relevant information to answer your question."
            ),
            "citations": [],
            "confidence": 0.0,
        }

    prompt = _build_rag_prompt(query, results[:5])

    trace_id = str(uuid4())
    prompt_tokens = _estimate_tokens(prompt)
    completion_tokens = 0
    model = settings.generation_model

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.llm_gateway_url}/v1/chat/completions",
                json={
                    "messages": [
                        {"role": "system", "content": _RAG_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "model": model,
                    "temperature": 0.3,
                    "max_tokens": 1024,
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()
            answer_text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            prompt_tokens = int(
                usage.get("prompt_tokens", prompt_tokens) or prompt_tokens
            )
            completion_tokens = int(
                usage.get("completion_tokens", _estimate_tokens(answer_text))
                or _estimate_tokens(answer_text)
            )
    except Exception:
        answer_text = (
            "I encountered an error while generating the answer. "
            "Here are the relevant context excerpts:\n\n"
            + "\n---\n".join(r.content[:300] for r in results[:3])
        )
        completion_tokens = _estimate_tokens(answer_text)

    citations = []
    chunk_ids = [r.chunk_id for r in results[:3]]
    chunks = await index.get_chunks_by_ids_async(chunk_ids)
    chunks_map = {str(c["id"]): c for c in chunks}

    doc_ids = []
    for c in chunks:
        if c.get("document_id"):
            doc_ids.append(str(c["document_id"]))
    for r in results[:3]:
        if r.document_id:
            doc_ids.append(str(r.document_id))
    doc_ids = list(set(doc_ids))
    docs = await index.get_documents_by_ids_async(doc_ids)
    docs_map = {str(d["id"]): d for d in docs}

    for result in results[:3]:
        chunk = chunks_map.get(str(result.chunk_id))
        if not chunk:
            chunk = {
                "id": result.chunk_id,
                "document_id": result.document_id,
                "content": result.content,
                "metadata": result.metadata,
            }
        doc = docs_map.get(str(chunk.get("document_id")))
        citations.append(_chunk_to_citation(chunk, result.score, doc=doc).model_dump())

    confidence = min(results[0].score, 1.0) if results else 0.0
    await _emit_cost_trace(
        trace_id=trace_id,
        query=query,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_cost_usd=calculate_cost(model, prompt_tokens, completion_tokens),
    )

    return {
        "answer": answer_text,
        "citations": citations,
        "confidence": confidence,
    }


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


async def _emit_cost_trace(
    trace_id: str,
    query: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_cost_usd: float,
) -> None:
    start = datetime.now(timezone.utc)
    span = {
        "trace_id": trace_id,
        "span_id": str(uuid4()),
        "parent_span_id": None,
        "service": "retrieval-service",
        "operation": "answer_generation",
        "start_time": start.isoformat(),
        "end_time": datetime.now(timezone.utc).isoformat(),
        "attributes": {
            "query": query,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_cost_usd": total_cost_usd,
            "status": "ok",
        },
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{settings.trace_service_url}/traces/ingest", json={"spans": [span]}
            )
    except Exception:
        return
