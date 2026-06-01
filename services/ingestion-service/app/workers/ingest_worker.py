"""Ingestion worker and API routes for document processing."""

import asyncio
import os
import tempfile
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.config import IngestionSettings
from app.db.session import async_session_factory, db_available
from app.models.chunk import Chunk
from app.models.document import Document
from app.parsers import PARSERS
from app.parsers.base import ParseResult
from app.processing.chunking import chunk_text
from app.processing.deduplication import compute_hash
from app.processing.versioning import get_next_version

router = APIRouter(prefix="/ingest")
settings = IngestionSettings()

_documents_store: dict[str, dict[str, Any]] = {}
_chunks_store: dict[str, list[dict[str, Any]]] = {}
_jobs_store: dict[str, dict[str, Any]] = {}


async def _generate_embedding(text: str) -> list[float] | None:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.llm_gateway_url}/v1/embeddings",
                json={"input": text, "model": "text-embedding-3-small"},
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return list(data["data"][0]["embedding"])
    except Exception:
        return None


async def _persist_document(doc_data: dict[str, Any]) -> None:
    async with async_session_factory() as session:
        document = Document(
            id=doc_data["id"],
            title=doc_data["title"],
            source=doc_data["source"],
            content_hash=doc_data["content_hash"],
            version=doc_data["version"],
            status=doc_data["status"],
            metadata_=doc_data.get("metadata", {}),
        )
        session.add(document)
        await session.commit()
        # Mirror version to document_versions audit table
        await session.execute(
            text(
                """
                INSERT INTO document_versions (document_id, version_number, content_hash)
                VALUES (:document_id, :version_number, :content_hash)
                ON CONFLICT (document_id, version_number) DO UPDATE SET
                    content_hash = EXCLUDED.content_hash
                """
            ),
            {
                "document_id": doc_data["id"],
                "version_number": doc_data["version"],
                "content_hash": doc_data["content_hash"],
            },
        )
        await session.commit()


async def _persist_chunks(
    doc_id: str, chunks_data: list[dict[str, Any]]
) -> None:
    async with async_session_factory() as session:
        for chunk_data in chunks_data:
            chunk = Chunk(
                id=chunk_data["id"],
                document_id=doc_id,
                content=chunk_data["content"],
                chunk_index=chunk_data["chunk_index"],
                content_hash=chunk_data["content_hash"],
                embedding=chunk_data.get("embedding"),
                metadata_=chunk_data.get("metadata", {}),
            )
            session.add(chunk)
        await session.commit()


async def _process_document_background(
    job_id: str,
    doc_id: str,
    parse_result: ParseResult,
    filename: str,
    content_hash: str,
    version: int,
) -> None:
    _jobs_store[job_id] = {
        "job_id": job_id,
        "document_id": doc_id,
        "status": "processing",
        "progress": 0,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        chunks = chunk_text(parse_result.content)
        _jobs_store[job_id]["progress"] = 30

        chunks_data: list[dict[str, Any]] = []
        total = len(chunks)

        for i, chunk in enumerate(chunks):
            embedding = await _generate_embedding(chunk.content)
            chunks_data.append(
                {
                    "id": str(uuid4()),
                    "document_id": doc_id,
                    "content": chunk.content,
                    "chunk_index": chunk.index,
                    "content_hash": compute_hash(chunk.content),
                    "embedding": embedding,
                    "metadata": chunk.metadata,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            _jobs_store[job_id]["progress"] = 30 + int(60 * (i + 1) / max(total, 1))

        _jobs_store[job_id]["progress"] = 90

        doc_data = {
            "id": doc_id,
            "title": parse_result.title,
            "source": filename,
            "content_hash": content_hash,
            "version": version,
            "status": "completed",
            "metadata": parse_result.metadata,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        _documents_store[doc_id] = doc_data
        _chunks_store[doc_id] = chunks_data

        await _persist_document(doc_data)
        await _persist_chunks(doc_id, chunks_data)

        _jobs_store[job_id]["status"] = "completed"
        _jobs_store[job_id]["progress"] = 100
        _jobs_store[job_id]["chunk_count"] = len(chunks)
    except Exception as exc:
        _jobs_store[job_id]["status"] = "failed"
        _jobs_store[job_id]["error"] = str(exc)


class DocumentResponse(BaseModel):
    """Response for document operations.

    Attributes:
        id: Document identifier.
        title: Document title.
        source: Original filename.
        status: Processing status.
        version: Document version.
        chunk_count: Number of extracted chunks.
        created_at: Creation timestamp.
    """

    id: str = Field(description="Document identifier")
    title: str = Field(description="Document title")
    source: str = Field(description="Original filename")
    status: str = Field(description="Processing status")
    version: int = Field(description="Document version")
    chunk_count: int = Field(description="Number of chunks")
    created_at: str = Field(description="Creation timestamp")


class JobResponse(BaseModel):
    """Response for processing job status.

    Attributes:
        job_id: Job identifier.
        document_id: Associated document identifier.
        status: Job status.
        progress: Progress percentage (0-100).
    """

    job_id: str = Field(description="Job identifier")
    document_id: str = Field(description="Document identifier")
    status: str = Field(description="Job status")
    progress: int = Field(description="Progress percentage")


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)) -> DocumentResponse:
    """Upload a document for ingestion.

    Parses the document, then starts background processing for
    chunking, embedding generation, and DB persistence.

    Args:
        file: Uploaded file (PDF, MD, HTML, or DOCX).

    Returns:
        Document metadata with processing status.
    """
    ext = os.path.splitext(file.filename or "unknown")[1].lower()
    parser = PARSERS.get(ext)

    if parser is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {ext}. Supported: {', '.join(PARSERS.keys())}",
        )

    content = await file.read()
    doc_id = str(uuid4())
    job_id = str(uuid4())
    version = await get_next_version(file.filename or "unknown")
    filename = file.filename or "unknown"

    with tempfile.NamedTemporaryFile(suffix=ext, delete=True) as tmp:
        tmp.write(content)
        tmp.flush()
        tmp.seek(0)
        parse_result = parser.parse(tmp, filename)

    content_hash = compute_hash(parse_result.content)

    _jobs_store[job_id] = {
        "job_id": job_id,
        "document_id": doc_id,
        "status": "parsing",
        "progress": 10,
    }

    from app.workers.queue import enqueue_ingestion

    await enqueue_ingestion(
        job_id=job_id,
        doc_id=doc_id,
        parse_result=parse_result,
        filename=filename,
        content_hash=content_hash,
        version=version,
    )

    created_at = datetime.now(timezone.utc).isoformat()

    return DocumentResponse(
        id=doc_id,
        title=parse_result.title,
        source=filename,
        status="processing",
        version=version,
        chunk_count=0,
        created_at=created_at,
    )


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents() -> list[DocumentResponse]:
    """List all ingested documents.

    Returns:
        List of document metadata.
    """
    if db_available:
        async with async_session_factory() as session:
            rows = await session.execute(
                text(
                    """
                    SELECT d.id, d.title, d.source, d.status, d.version, d.created_at,
                           COUNT(c.id) AS chunk_count
                    FROM documents d
                    LEFT JOIN chunks c ON c.document_id = d.id
                    GROUP BY d.id
                    ORDER BY d.created_at DESC
                    """
                )
            )
            return [
                DocumentResponse(
                    id=str(row["id"]),
                    title=row["title"],
                    source=row["source"],
                    status=row["status"],
                    version=row["version"],
                    chunk_count=row["chunk_count"] or 0,
                    created_at=str(row["created_at"]) if row["created_at"] else "",
                )
                for row in rows.mappings()
            ]

    return [
        DocumentResponse(
            id=doc["id"],
            title=doc["title"],
            source=doc["source"],
            status=doc["status"],
            version=doc["version"],
            chunk_count=len(_chunks_store.get(doc["id"], [])),
            created_at=doc["created_at"],
        )
        for doc in _documents_store.values()
    ]


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str) -> dict[str, Any]:
    """Get document details by ID.

    Args:
        doc_id: Document identifier.

    Returns:
        Full document metadata with chunks.
    """
    if db_available:
        async with async_session_factory() as session:
            doc_row = await session.execute(
                text("SELECT * FROM documents WHERE id = :id"),
                {"id": doc_id},
            )
            doc = doc_row.mappings().one_or_none()
            if doc is None:
                raise HTTPException(status_code=404, detail="Document not found")
            chunk_rows = await session.execute(
                text("SELECT id, content, chunk_index, metadata FROM chunks WHERE document_id = :doc_id"),
                {"doc_id": doc_id},
            )
            chunks = [
                {
                    "id": str(row["id"]),
                    "content": row["content"],
                    "chunk_index": row["chunk_index"],
                    "metadata": row["metadata"] or {},
                }
                for row in chunk_rows.mappings()
            ]
            return {
                "id": str(doc["id"]),
                "title": doc["title"],
                "source": doc["source"],
                "status": doc["status"],
                "version": doc["version"],
                "metadata": doc["metadata"] or {},
                "created_at": str(doc["created_at"]) if doc["created_at"] else "",
                "updated_at": str(doc["updated_at"]) if doc["updated_at"] else "",
                "chunks": chunks,
            }

    if doc_id not in _documents_store:
        raise HTTPException(status_code=404, detail="Document not found")
    return _documents_store[doc_id]


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str) -> dict[str, str]:
    """Delete a document and its chunks.

    Args:
        doc_id: Document identifier.

    Returns:
        Confirmation message.
    """
    if db_available:
        async with async_session_factory() as session:
            await session.execute(
                text("DELETE FROM chunks WHERE document_id = :doc_id"),
                {"doc_id": doc_id},
            )
            result = await session.execute(
                text("DELETE FROM documents WHERE id = :id RETURNING id"),
                {"id": doc_id},
            )
            if result.scalar_one_or_none() is None:
                raise HTTPException(status_code=404, detail="Document not found")
            await session.commit()

    if doc_id in _documents_store:
        del _documents_store[doc_id]
    _chunks_store.pop(doc_id, None)
    return {"message": f"Document {doc_id} deleted"}


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str) -> JobResponse:
    """Get processing job status.

    Args:
        job_id: Job identifier.

    Returns:
        Job status with progress.
    """
    job = _jobs_store.get(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        job_id=job["job_id"],
        document_id=job["document_id"],
        status=job["status"],
        progress=job["progress"],
    )



