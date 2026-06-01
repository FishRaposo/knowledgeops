"""Trace replay engine for reproducing past request chains."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.collector.trace_collector import _traces_store
from app.db.session import async_session_factory, db_available
from app.storage.trace_store import _span_from_row

router = APIRouter(prefix="/traces")


class ReplayRequest(BaseModel):
    """Request to replay a trace.

    Attributes:
        trace_id: Trace identifier to replay.
        dry_run: If True, return replay plan without executing.
    """

    trace_id: str = Field(description="Trace ID to replay")
    dry_run: bool = Field(default=True, description="Preview without executing")


class ReplayResult(BaseModel):
    """Result of a trace replay.

    Attributes:
        trace_id: Replayed trace identifier.
        status: Replay status.
        operations: List of operations that would be replayed.
        message: Human-readable result message.
    """

    trace_id: str
    status: str
    operations: list[dict[str, Any]]
    message: str


@router.post("/{trace_id}/replay", response_model=ReplayResult)
async def replay_trace(trace_id: str, dry_run: bool = True) -> ReplayResult:
    """Replay a trace to reproduce a past request chain.

    Args:
        trace_id: Trace identifier to replay.
        dry_run: If True, return plan without executing.

    Returns:
        Replay result with operation plan.
    """
    if db_available:
        async with async_session_factory() as session:
            rows = await session.execute(
                text("SELECT * FROM trace_spans WHERE trace_id = :trace_id ORDER BY start_time"),
                {"trace_id": trace_id},
            )
            spans = [_span_from_row(row) for row in rows.mappings()]
    else:
        spans = sorted(
            _traces_store.get(trace_id, []),
            key=lambda span: span.get("start_time", ""),
        )

    operations = [
        {
            "service": span.get("service", "unknown"),
            "operation": span.get("operation", "unknown"),
            "span_id": span.get("span_id"),
            "attributes": span.get("attributes", {}),
            "replayed": not dry_run,
        }
        for span in spans
    ]

    if not operations:
        operations = [
            {
                "service": "unknown",
                "operation": "not_found",
                "note": "No spans were found for this trace id.",
                "replayed": False,
            }
        ]

    return ReplayResult(
        trace_id=trace_id,
        status="dry_run" if dry_run else "replayed",
        operations=operations,
        message=f"Trace replay {'planned' if dry_run else 'executed'} for {trace_id} with {len(spans)} span(s)",
    )
