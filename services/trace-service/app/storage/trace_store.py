"""Trace storage with query and filtering capabilities."""

from typing import Any

from fastapi import APIRouter, Query

from app.collector.trace_collector import _traces_store
from app.config import TraceSettings

router = APIRouter()
settings = TraceSettings()


@router.get("/traces")
async def list_traces(
    service: str | None = Query(default=None, description="Filter by service"),
    limit: int = Query(default=50, ge=1, le=200, description="Max results"),
) -> list[dict[str, Any]]:
    """Query traces with optional filtering.

    Args:
        service: Optional service name filter.
        limit: Maximum number of results.

    Returns:
        List of trace spans matching the filters.
    """
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
    """Get all spans for a specific trace.

    Args:
        trace_id: Trace identifier.

    Returns:
        Trace data with all associated spans.
    """
    spans = _traces_store.get(trace_id, [])
    if not spans:
        return {"trace_id": trace_id, "spans": []}
    return {"trace_id": trace_id, "spans": spans}


@router.get("/traces/costs")
async def get_costs() -> dict[str, Any]:
    """Get cost summary aggregated from trace data.

    Returns:
        Cost summary by service and model.
    """
    by_service: dict[str, float] = {}
    by_model: dict[str, float] = {}
    by_user: dict[str, float] = {}
    cost_records: list[dict[str, Any]] = []
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_usd = 0.0

    for spans in _traces_store.values():
        for span in spans:
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

    for spans in _traces_store.values():
        for span in spans:
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
