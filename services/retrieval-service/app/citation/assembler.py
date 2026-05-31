"""Citation assembly for linking answers to source documents."""

from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.search.index import index

router = APIRouter(prefix="/retrieve/citations")


class CitationRequest(BaseModel):
    """Request for citation assembly.

    Attributes:
        chunk_ids: Chunk identifiers to create citations for.
        answer: Generated answer text.
    """

    chunk_ids: list[str] = Field(description="Chunk IDs")
    answer: str = Field(description="Generated answer")


class Citation(BaseModel):
    """A citation linking an answer to source material.

    Attributes:
        id: Citation identifier.
        chunk_id: Source chunk identifier.
        document_id: Source document identifier.
        document_title: Document title for display.
        excerpt: Relevant excerpt from the source chunk.
        relevance_score: Relevance to the cited claim.
    """

    id: str
    chunk_id: str
    document_id: str
    document_title: str
    excerpt: str
    relevance_score: float


def _chunk_to_citation(
    chunk: dict[str, object], score: float = 0.85
) -> Citation:
    doc_id = str(chunk.get("document_id", "unknown"))
    doc = index.get_document(doc_id)
    document_title = (
        str(doc["title"]) if doc and doc.get("title")
        else str(chunk.get("metadata", {}).get("title", "Document"))
        if isinstance(chunk.get("metadata"), dict)
        else "Document"
    )
    content = str(chunk.get("content", ""))
    return Citation(
        id=str(uuid4()),
        chunk_id=str(chunk.get("id", "")),
        document_id=doc_id,
        document_title=document_title,
        excerpt=content[:200] if len(content) > 200 else content,
        relevance_score=score,
    )


@router.post("/assemble")
async def assemble_citations(request: CitationRequest) -> list[Citation]:
    """Assemble citations from chunk IDs and answer text.

    Looks up chunk data from the in-memory index and constructs
    proper citations with real document titles and excerpts.
    """
    chunks = index.get_chunks_by_ids(request.chunk_ids)
    return [_chunk_to_citation(c) for c in chunks]


@router.get("/{doc_id}")
async def get_document_citations(doc_id: str) -> list[Citation]:
    """Get all citations for a document."""
    chunks = index.get_chunks_by_document(doc_id)
    return [_chunk_to_citation(c) for c in chunks]
