"""Trace collector API for receiving trace spans from services."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.db.session import async_session_factory, db_available

router = APIRouter(prefix="/traces")

_traces_store: dict[str, list[dict[str, Any]]] = {}


class SpanInput(BaseModel):
    """Input span data for ingestion.

    Attributes:
        trace_id: Trace identifier shared across related spans.
        span_id: Unique span identifier.
        parent_span_id: Parent span for nesting.
        service: Service that generated the span.
        operation: Operation name.
        start_time: Span start timestamp.
        end_time: Span end timestamp.
        attributes: Additional span attributes.
    """

    trace_id: str = Field(description="Trace identifier")
    span_id: str = Field(description="Span identifier")
    parent_span_id: str | None = Field(default=None, description="Parent span ID")
    service: str = Field(description="Service name")
    operation: str = Field(description="Operation name")
    start_time: str = Field(description="Start timestamp")
    end_time: str = Field(description="End timestamp")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Span attributes")


class IngestRequest(BaseModel):
    """Request to ingest one or more trace spans.

    Attributes:
        spans: List of span data to ingest.
    """

    spans: list[SpanInput] = Field(description="Spans to ingest")


class IngestResponse(BaseModel):
    """Response from span ingestion.

    Attributes:
        ingested: Number of spans ingested.
        trace_ids: Unique trace identifiers from the batch.
    """

    ingested: int = Field(description="Count of ingested spans")
    trace_ids: list[str] = Field(description="Unique trace IDs")


@router.post("/ingest", response_model=IngestResponse)
async def ingest_spans(request: IngestRequest) -> IngestResponse:
    """Ingest trace spans from any service.

    Writes to PostgreSQL when available, always mirrors to the
    in-memory store so a DB outage never loses observability.

    Args:
        request: Ingest request with span data.

    Returns:
        Count of ingested spans and trace IDs.
    """
    trace_ids: set[str] = set()

    for span in request.spans:
        if span.trace_id not in _traces_store:
            _traces_store[span.trace_id] = []
        _traces_store[span.trace_id].append(span.model_dump())
        trace_ids.add(span.trace_id)

    if db_available:
        await _persist_spans_to_db(request.spans)

    return IngestResponse(ingested=len(request.spans), trace_ids=list(trace_ids))


async def _persist_spans_to_db(spans: list[SpanInput]) -> None:
    """Insert spans into the trace_spans table and cost records table."""
    async with async_session_factory() as session:
        for span in spans:
            await session.execute(
                text(
                    """
                    INSERT INTO trace_spans (trace_id, span_id, parent_span_id, service, operation, start_time, end_time, attributes)
                    VALUES (:trace_id, :span_id, :parent_span_id, :service, :operation, :start_time, :end_time, :attributes)
                    """
                ),
                {
                    "trace_id": span.trace_id,
                    "span_id": span.span_id,
                    "parent_span_id": span.parent_span_id,
                    "service": span.service,
                    "operation": span.operation,
                    "start_time": span.start_time,
                    "end_time": span.end_time,
                    "attributes": span.attributes,
                },
            )

            # Check if span contains cost attributes and write to cost_records table
            attrs = span.attributes
            if attrs and (attrs.get("total_cost_usd") or attrs.get("prompt_tokens") or attrs.get("completion_tokens")):
                cost = float(attrs.get("total_cost_usd", 0.0) or 0.0)
                prompt_tokens = int(attrs.get("prompt_tokens", 0) or 0)
                completion_tokens = int(attrs.get("completion_tokens", 0) or 0)
                model = str(attrs.get("model", "unknown"))
                user_id_str = attrs.get("user_id")

                user_uuid = None
                if user_id_str:
                    try:
                        from uuid import UUID
                        temp_uuid = UUID(str(user_id_str))
                        # Verify user_id exists in users table to prevent Foreign Key violations
                        res = await session.execute(
                            text("SELECT id FROM users WHERE id = :id"),
                            {"id": temp_uuid}
                        )
                        if res.scalar() is not None:
                            user_uuid = temp_uuid
                    except Exception:
                        user_uuid = None

                await session.execute(
                    text(
                        """
                        INSERT INTO cost_records (service, user_id, model, prompt_tokens, completion_tokens, total_cost_usd, request_id, created_at)
                        VALUES (:service, :user_id, :model, :prompt_tokens, :completion_tokens, :total_cost_usd, :request_id, :created_at)
                        """
                    ),
                    {
                        "service": span.service,
                        "user_id": user_uuid,
                        "model": model,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_cost_usd": cost,
                        "request_id": span.trace_id,
                        "created_at": span.end_time,
                    }
                )
        await session.commit()
