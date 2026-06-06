"""Trace storage with query and filtering capabilities."""

from typing import Any

from fastapi import APIRouter, Query
from sqlalchemy import text

from app.collector.trace_collector import _traces_store
from app.config import TraceSettings
from app.db.session import async_session_factory, db_available

router = APIRouter()
settings = TraceSettings()


def _span_from_row(row: Any) -> dict[str, Any]:
    """Convert a trace_spans DB row to the in-memory dict shape."""
    return {
        "trace_id": str(row["trace_id"]),
        "span_id": str(row["span_id"]),
        "parent_span_id": str(row["parent_span_id"]) if row["parent_span_id"] else None,
        "service": row["service"],
        "operation": row["operation"],
        "start_time": str(row["start_time"]),
        "end_time": str(row["end_time"]),
        "attributes": row["attributes"] or {},
    }


async def _all_spans_from_db(service: str | None = None) -> list[dict[str, Any]]:
    """Fetch all spans from the database, optionally filtered by service."""
    async with async_session_factory() as session:
        if service:
            rows = await session.execute(
                text("SELECT * FROM trace_spans WHERE service = :service ORDER BY start_time DESC"),
                {"service": service},
            )
        else:
            rows = await session.execute(
                text("SELECT * FROM trace_spans ORDER BY start_time DESC")
            )
        return [_span_from_row(row) for row in rows.mappings()]


@router.get("/traces")
async def list_traces(
    service: str | None = Query(default=None, description="Filter by service"),
    limit: int = Query(default=50, ge=1, le=200, description="Max results"),
) -> list[dict[str, Any]]:
    """Query traces with optional filtering.

    Reads from PostgreSQL when available, otherwise falls back to the
    in-memory store.
    """
    if db_available:
        results = await _all_spans_from_db(service=service)
        return results[:limit]

    results: list[dict[str, Any]] = []
    for trace_id, spans in _traces_store.items():
        for span in spans:
            if service and span.get("service") != service:
                continue
            results.append(span)
            if len(results) >= limit:
                return results
    return results


@router.get("/traces/{trace_id}")
async def get_trace(trace_id: str) -> dict[str, Any]:
    """Get all spans for a specific trace."""
    if db_available:
        async with async_session_factory() as session:
            rows = await session.execute(
                text("SELECT * FROM trace_spans WHERE trace_id = :trace_id ORDER BY start_time"),
                {"trace_id": trace_id},
            )
            spans = [_span_from_row(row) for row in rows.mappings()]
            return {"trace_id": trace_id, "spans": spans}

    spans = _traces_store.get(trace_id, [])
    return {"trace_id": trace_id, "spans": spans}


async def _get_all_spans_for_aggregation() -> list[dict[str, Any]]:
    """Return every span for cost/alert aggregation."""
    if db_available:
        return await _all_spans_from_db()
    spans: list[dict[str, Any]] = []
    for trace_spans in _traces_store.values():
        spans.extend(trace_spans)
    return spans


@router.get("/traces/costs")
async def get_costs() -> dict[str, Any]:
    """Get cost summary aggregated from trace data."""
    if db_available:
        async with async_session_factory() as session:
            # 1. Total and token sums
            res = await session.execute(
                text(
                    """
                    SELECT COALESCE(SUM(total_cost_usd), 0) AS total_usd,
                           COALESCE(SUM(prompt_tokens), 0) AS total_prompt_tokens,
                           COALESCE(SUM(completion_tokens), 0) AS total_completion_tokens
                    FROM cost_records
                    """
                )
            )
            agg = res.mappings().one()
            total_usd = float(agg["total_usd"])
            total_prompt_tokens = int(agg["total_prompt_tokens"])
            total_completion_tokens = int(agg["total_completion_tokens"])

            # 2. Group by service
            res = await session.execute(
                text("SELECT service, COALESCE(SUM(total_cost_usd), 0) AS cost FROM cost_records GROUP BY service")
            )
            by_service = {row["service"]: float(row["cost"]) for row in res.mappings()}

            # 3. Group by model
            res = await session.execute(
                text("SELECT model, COALESCE(SUM(total_cost_usd), 0) AS cost FROM cost_records GROUP BY model")
            )
            by_model = {row["model"]: float(row["cost"]) for row in res.mappings()}

            # 4. Group by user
            res = await session.execute(
                text("SELECT COALESCE(user_id::text, 'anonymous') AS user_id, COALESCE(SUM(total_cost_usd), 0) AS cost FROM cost_records GROUP BY user_id")
            )
            by_user = {row["user_id"]: float(row["cost"]) for row in res.mappings()}

            # 5. Detail cost records
            res = await session.execute(
                text(
                    """
                    SELECT id, service, COALESCE(user_id::text, 'anonymous') AS user_id, model,
                           prompt_tokens, completion_tokens, total_cost_usd, request_id, created_at
                    FROM cost_records
                    ORDER BY created_at DESC
                    LIMIT 100
                    """
                )
            )
            cost_records = [
                {
                    "id": str(row["id"]),
                    "service": row["service"],
                    "user_id": row["user_id"],
                    "model": row["model"],
                    "prompt_tokens": row["prompt_tokens"],
                    "completion_tokens": row["completion_tokens"],
                    "total_cost_usd": float(row["total_cost_usd"]),
                    "request_id": row["request_id"],
                    "created_at": str(row["created_at"]) if row["created_at"] else "",
                }
                for row in res.mappings()
            ]

            return {
                "total_usd": round(total_usd, 6),
                "by_service": {k: round(v, 6) for k, v in by_service.items()},
                "by_model": {k: round(v, 6) for k, v in by_model.items()},
                "by_user": {k: round(v, 6) for k, v in by_user.items()},
                "total_prompt_tokens": total_prompt_tokens,
                "total_completion_tokens": total_completion_tokens,
                "costs": cost_records,
            }

    all_spans = await _get_all_spans_for_aggregation()

    by_service: dict[str, float] = {}
    by_model: dict[str, float] = {}
    by_user: dict[str, float] = {}
    cost_records: list[dict[str, Any]] = []
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_usd = 0.0

    for span in all_spans:
        attrs = span.get("attributes", {})
        if not attrs:
            continue

        cost = float(attrs.get("total_cost_usd", 0.0) or 0.0)
        prompt_tokens = int(attrs.get("prompt_tokens", 0) or 0)
        completion_tokens = int(attrs.get("completion_tokens", 0) or 0)
        model = attrs.get("model", "unknown")
        service = span.get("service", "unknown")
        user_id = str(attrs.get("user_id", "anonymous"))

        if cost <= 0 and prompt_tokens <= 0 and completion_tokens <= 0:
            continue

        total_usd += cost
        total_prompt_tokens += prompt_tokens
        total_completion_tokens += completion_tokens

        by_service[service] = by_service.get(service, 0.0) + cost
        by_model[str(model)] = by_model.get(str(model), 0.0) + cost
        by_user[user_id] = by_user.get(user_id, 0.0) + cost
        cost_records.append(
            {
                "id": str(span.get("span_id", "")),
                "service": service,
                "user_id": user_id,
                "model": str(model),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_cost_usd": round(cost, 6),
                "request_id": str(span.get("trace_id", "")),
                "created_at": str(span.get("end_time") or span.get("start_time") or ""),
            }
        )

    return {
        "total_usd": round(total_usd, 6),
        "by_service": {k: round(v, 6) for k, v in by_service.items()},
        "by_model": {k: round(v, 6) for k, v in by_model.items()},
        "by_user": {k: round(v, 6) for k, v in by_user.items()},
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "costs": cost_records,
    }


@router.get("/alerts")
async def get_alerts(
    budget_limit_usd: float = Query(default=None, ge=0.0),
) -> dict[str, Any]:
    """Return budget and service failure alerts derived from trace data."""
    limit = settings.budget_alert_limit_usd if budget_limit_usd is None else budget_limit_usd
    cost_summary = await get_costs()
    alerts: list[dict[str, Any]] = []

    if cost_summary["total_usd"] > limit:
        alerts.append(
            {
                "type": "budget_overrun",
                "severity": "critical",
                "message": f"Total spend ${cost_summary['total_usd']:.2f} exceeds limit ${limit:.2f}.",
                "current_value": cost_summary["total_usd"],
                "threshold": limit,
            }
        )

    if db_available:
        async with async_session_factory() as session:
            # Query trace_spans table directly for failures
            res = await session.execute(
                text(
                    """
                    SELECT service, operation, trace_id, span_id, attributes
                    FROM trace_spans
                    WHERE attributes->>'status' IN ('error', 'failed') OR attributes->>'error' IS NOT NULL
                    """
                )
            )
            for row in res.mappings():
                alerts.append(
                    {
                        "type": "service_failure",
                        "severity": "warning",
                        "message": f"{row['service']} reported {row['operation']} failure.",
                        "trace_id": row["trace_id"],
                        "span_id": row["span_id"],
                    }
                )
    else:
        all_spans = await _get_all_spans_for_aggregation()
        for span in all_spans:
            attrs = span.get("attributes", {})
            if attrs.get("status") in {"error", "failed"} or attrs.get("error"):
                alerts.append(
                    {
                        "type": "service_failure",
                        "severity": "warning",
                        "message": f"{span.get('service', 'unknown')} reported {span.get('operation', 'unknown')} failure.",
                        "trace_id": span.get("trace_id"),
                        "span_id": span.get("span_id"),
                    }
                )

    return {"alerts": alerts, "total": len(alerts), "budget_limit_usd": limit}
