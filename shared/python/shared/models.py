"""Shared Pydantic models for KnowledgeOps services."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    """Document processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(BaseModel):
    """A document in the knowledge base.

    Attributes:
        id: Unique document identifier.
        title: Document title.
        source: Original source filename or URI.
        content_hash: SHA-256 hash of raw content.
        version: Document version, incremented on re-ingestion.
        status: Current processing status.
        metadata: Arbitrary key-value metadata.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    id: UUID = Field(description="Unique document identifier")
    title: str = Field(description="Document title")
    source: str = Field(description="Original source filename or URI")
    content_hash: str = Field(description="SHA-256 hash of raw content")
    version: int = Field(default=1, description="Document version")
    status: DocumentStatus = Field(
        default=DocumentStatus.PENDING, description="Processing status"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary metadata"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Update timestamp"
    )


class Chunk(BaseModel):
    """A text chunk extracted from a document.

    Attributes:
        id: Unique chunk identifier.
        document_id: Parent document identifier.
        content: Chunk text content.
        chunk_index: Position within the parent document.
        content_hash: SHA-256 hash of chunk content.
        metadata: Arbitrary key-value metadata including token count.
        created_at: Creation timestamp.
    """

    id: UUID = Field(description="Unique chunk identifier")
    document_id: UUID = Field(description="Parent document identifier")
    content: str = Field(description="Chunk text content")
    chunk_index: int = Field(description="Position within parent document")
    content_hash: str = Field(description="SHA-256 hash of chunk content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )


class Citation(BaseModel):
    """A citation linking an answer claim to a source chunk.

    Attributes:
        chunk_id: Source chunk identifier.
        document_id: Source document identifier.
        document_title: Document title for display.
        excerpt: Relevant excerpt from the source chunk.
        relevance_score: Relevance of the citation to the claim.
    """

    chunk_id: UUID = Field(description="Source chunk identifier")
    document_id: UUID = Field(description="Source document identifier")
    document_title: str = Field(description="Document title for display")
    excerpt: str = Field(description="Relevant excerpt from source chunk")
    relevance_score: float = Field(ge=0.0, le=1.0, description="Relevance score")


class QueryRequest(BaseModel):
    """A retrieval query request.

    Attributes:
        query: Natural language question.
        top_k: Number of results to retrieve.
        include_metadata: Whether to include chunk metadata in response.
        filters: Optional document-level filters.
    """

    query: str = Field(description="Natural language question")
    top_k: int = Field(
        default=5, ge=1, le=50, description="Number of results to retrieve"
    )
    include_metadata: bool = Field(default=True, description="Include chunk metadata")
    filters: dict[str, Any] = Field(
        default_factory=dict, description="Document filters"
    )


class QueryResponse(BaseModel):
    """A retrieval query response.

    Attributes:
        answer: Generated response text.
        citations: Source citations for the answer.
        refusal: Whether the system refused to answer.
        refusal_reason: Reason for refusal if applicable.
        chunks_used: IDs of chunks used in generation.
        confidence: Overall confidence score.
        query: The original query string.
    """

    answer: str = Field(description="Generated response text")
    citations: list[Citation] = Field(
        default_factory=list, description="Source citations"
    )
    refusal: bool = Field(default=False, description="Whether answer was refused")
    refusal_reason: Optional[str] = Field(default=None, description="Refusal reason")
    chunks_used: list[UUID] = Field(default_factory=list, description="Chunk IDs used")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence score"
    )
    query: str = Field(description="Original query string")


class User(BaseModel):
    """A platform user.

    Attributes:
        id: Unique user identifier.
        email: User email address.
        name: Display name.
        role: RBAC role (admin, user, viewer).
        created_at: Account creation timestamp.
    """

    id: UUID = Field(description="Unique user identifier")
    email: str = Field(description="User email address")
    name: str = Field(description="Display name")
    role: str = Field(default="viewer", description="RBAC role")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )


class EvalRun(BaseModel):
    """An evaluation run.

    Attributes:
        id: Unique run identifier.
        name: Descriptive name for the run.
        status: Current run status.
        config: Run configuration.
        started_at: When the run started.
        completed_at: When the run completed.
    """

    id: UUID = Field(description="Unique run identifier")
    name: str = Field(description="Run name")
    status: str = Field(default="pending", description="Run status")
    config: dict[str, Any] = Field(
        default_factory=dict, description="Run configuration"
    )
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(
        default=None, description="Completion timestamp"
    )


class EvalResult(BaseModel):
    """A single evaluation result.

    Attributes:
        id: Unique result identifier.
        run_id: Parent run identifier.
        query: Test query.
        expected: Expected answer.
        actual: Actual answer from the system.
        scores: Judge scores.
        created_at: Result creation timestamp.
    """

    id: UUID = Field(description="Unique result identifier")
    run_id: UUID = Field(description="Parent run identifier")
    query: str = Field(description="Test query")
    expected: Optional[str] = Field(default=None, description="Expected answer")
    actual: Optional[str] = Field(default=None, description="Actual answer")
    scores: dict[str, float] = Field(default_factory=dict, description="Judge scores")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )


class TraceSpan(BaseModel):
    """A trace span for observability.

    Attributes:
        trace_id: Trace identifier shared across related spans.
        span_id: Unique span identifier.
        parent_span_id: Parent span identifier for nesting.
        service: Service that generated the span.
        operation: Operation name.
        start_time: Span start timestamp.
        end_time: Span end timestamp.
        attributes: Additional span attributes.
    """

    trace_id: str = Field(description="Trace identifier")
    span_id: str = Field(description="Span identifier")
    parent_span_id: Optional[str] = Field(
        default=None, description="Parent span identifier"
    )
    service: str = Field(description="Service name")
    operation: str = Field(description="Operation name")
    start_time: datetime = Field(description="Start timestamp")
    end_time: datetime = Field(description="End timestamp")
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Span attributes"
    )


class CostRecord(BaseModel):
    """An LLM cost record.

    Attributes:
        id: Unique record identifier.
        service: Service that incurred the cost.
        user_id: User associated with the request.
        model: LLM model used.
        prompt_tokens: Number of prompt tokens.
        completion_tokens: Number of completion tokens.
        total_cost_usd: Total cost in USD.
        request_id: Associated request identifier.
        created_at: Record creation timestamp.
    """

    id: UUID = Field(description="Unique record identifier")
    service: str = Field(description="Service name")
    user_id: Optional[UUID] = Field(default=None, description="User identifier")
    model: str = Field(description="LLM model used")
    prompt_tokens: int = Field(default=0, ge=0, description="Prompt token count")
    completion_tokens: int = Field(
        default=0, ge=0, description="Completion token count"
    )
    total_cost_usd: float = Field(default=0.0, ge=0.0, description="Cost in USD")
    request_id: Optional[str] = Field(default=None, description="Request identifier")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Record timestamp"
    )
