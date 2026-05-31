"""Trace collector API for receiving trace spans from services."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

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

    return IngestResponse(ingested=len(request.spans), trace_ids=list(trace_ids))
