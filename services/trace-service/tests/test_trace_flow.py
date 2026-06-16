"""Tests for trace collection, storage, cost aggregation, alerts, and replay."""

from typing import Any

import pytest
from app.collector import trace_collector
from httpx import AsyncClient


@pytest.fixture(autouse=True)
def _clear_store() -> None:
    trace_collector._traces_store.clear()
    yield
    trace_collector._traces_store.clear()


def _span(
    trace_id: str = "t1",
    span_id: str = "s1",
    service: str = "retrieval-service",
    operation: str = "answer_generation",
    attributes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": None,
        "service": service,
        "operation": operation,
        "start_time": "2026-01-01T00:00:00Z",
        "end_time": "2026-01-01T00:00:01Z",
        "attributes": attributes or {},
    }


# --- ingestion ---------------------------------------------------------------


@pytest.mark.asyncio
async def test_ingest_spans(client: AsyncClient) -> None:
    resp = await client.post(
        "/traces/ingest", json={"spans": [_span(), _span(span_id="s2")]}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ingested"] == 2
    assert body["trace_ids"] == ["t1"]


# --- storage / query ---------------------------------------------------------


@pytest.mark.asyncio
async def test_list_traces_and_filter_by_service(client: AsyncClient) -> None:
    await client.post(
        "/traces/ingest",
        json={
            "spans": [
                _span(span_id="s1", service="retrieval-service"),
                _span(trace_id="t2", span_id="s2", service="eval-service"),
            ]
        },
    )
    all_traces = await client.get("/traces")
    assert len(all_traces.json()) == 2

    filtered = await client.get("/traces", params={"service": "eval-service"})
    body = filtered.json()
    assert len(body) == 1
    assert body[0]["service"] == "eval-service"


@pytest.mark.asyncio
async def test_get_trace_by_id(client: AsyncClient) -> None:
    await client.post("/traces/ingest", json={"spans": [_span()]})
    resp = await client.get("/traces/t1")
    body = resp.json()
    assert body["trace_id"] == "t1"
    assert len(body["spans"]) == 1


@pytest.mark.asyncio
async def test_costs_route_not_shadowed_by_trace_id(client: AsyncClient) -> None:
    """Regression: ``/traces/costs`` must resolve to the cost summary, not be
    captured by the dynamic ``/traces/{trace_id}`` route."""
    resp = await client.get("/traces/costs")
    body = resp.json()
    assert "total_usd" in body
    assert "by_service" in body
    assert "trace_id" not in body


# --- cost aggregation --------------------------------------------------------


@pytest.mark.asyncio
async def test_costs_aggregates_by_service_model_user(client: AsyncClient) -> None:
    await client.post(
        "/traces/ingest",
        json={
            "spans": [
                _span(
                    span_id="s1",
                    attributes={
                        "total_cost_usd": 0.05,
                        "prompt_tokens": 100,
                        "completion_tokens": 50,
                        "model": "gpt-4o-mini",
                        "user_id": "alice",
                    },
                ),
                _span(
                    trace_id="t2",
                    span_id="s2",
                    service="eval-service",
                    attributes={
                        "total_cost_usd": 0.02,
                        "prompt_tokens": 20,
                        "completion_tokens": 10,
                        "model": "gpt-4o-mini",
                        "user_id": "bob",
                    },
                ),
            ]
        },
    )
    resp = await client.get("/traces/costs")
    body = resp.json()
    assert body["total_usd"] == pytest.approx(0.07)
    assert body["total_prompt_tokens"] == 120
    assert body["total_completion_tokens"] == 60
    assert body["by_service"]["retrieval-service"] == pytest.approx(0.05)
    assert body["by_model"]["gpt-4o-mini"] == pytest.approx(0.07)
    assert set(body["by_user"]) == {"alice", "bob"}
    assert len(body["costs"]) == 2


@pytest.mark.asyncio
async def test_costs_ignores_zero_cost_spans(client: AsyncClient) -> None:
    await client.post(
        "/traces/ingest",
        json={"spans": [_span(attributes={"status": "ok"})]},
    )
    resp = await client.get("/traces/costs")
    body = resp.json()
    assert body["total_usd"] == 0.0
    assert body["costs"] == []


# --- alerts ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_alerts_budget_overrun(client: AsyncClient) -> None:
    await client.post(
        "/traces/ingest",
        json={
            "spans": [
                _span(attributes={"total_cost_usd": 5.0, "model": "m", "user_id": "u"})
            ]
        },
    )
    resp = await client.get("/alerts", params={"budget_limit_usd": 1.0})
    body = resp.json()
    overruns = [a for a in body["alerts"] if a["type"] == "budget_overrun"]
    assert overruns
    assert overruns[0]["severity"] == "critical"


@pytest.mark.asyncio
async def test_alerts_service_failure(client: AsyncClient) -> None:
    await client.post(
        "/traces/ingest",
        json={"spans": [_span(attributes={"status": "error"})]},
    )
    resp = await client.get("/alerts", params={"budget_limit_usd": 1000.0})
    body = resp.json()
    failures = [a for a in body["alerts"] if a["type"] == "service_failure"]
    assert failures
    assert failures[0]["severity"] == "warning"


@pytest.mark.asyncio
async def test_alerts_none_when_clean(client: AsyncClient) -> None:
    resp = await client.get("/alerts", params={"budget_limit_usd": 1000.0})
    body = resp.json()
    assert body["alerts"] == []
    assert body["total"] == 0


# --- replay ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_replay_dry_run(client: AsyncClient) -> None:
    await client.post(
        "/traces/ingest",
        json={"spans": [_span(operation="query", attributes={"query": "hello"})]},
    )
    resp = await client.post("/traces/t1/replay", params={"dry_run": True})
    body = resp.json()
    assert body["status"] == "dry_run"
    assert body["operations"]
    assert body["operations"][0]["replayed"] is False


@pytest.mark.asyncio
async def test_replay_missing_trace_returns_not_found_op(client: AsyncClient) -> None:
    resp = await client.post("/traces/missing/replay", params={"dry_run": True})
    body = resp.json()
    assert body["operations"][0]["operation"] == "not_found"


# --- bounded in-memory fallback ----------------------------------------------


def test_trace_store_is_bounded_fifo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: the in-memory trace fallback must not grow without bound.

    With the cap lowered to 3, inserting a 4th distinct trace evicts the
    oldest one (FIFO) while keeping the newest entries.
    """
    monkeypatch.setattr(trace_collector, "_MAX_TRACES", 3)
    store = trace_collector._BoundedTraceStore()
    for i in range(5):
        store[f"t{i}"] = [_span(trace_id=f"t{i}")]
    assert len(store) == 3
    # Oldest two evicted; newest three retained, oldest-first order preserved.
    assert list(store.keys()) == ["t2", "t3", "t4"]
    assert "t0" not in store
    assert "t4" in store
