"""Local service behavior tests that do not require Docker."""

import asyncio
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _reset_app_modules() -> None:
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            del sys.modules[name]


def test_reranker_promotes_query_relevant_content() -> None:
    module = _load_module(
        "reranking",
        ROOT / "services" / "retrieval-service" / "app" / "search" / "reranking.py",
    )
    results = [
        module.RankedResult(
            chunk_id="a",
            document_id="d1",
            content="General onboarding notes",
            score=0.8,
        ),
        module.RankedResult(
            chunk_id="b",
            document_id="d2",
            content="Refund policy allows returns within thirty days",
            score=0.4,
        ),
    ]

    reranked = module.rerank_results(results, "refund policy", top_k=2)

    assert reranked[0].chunk_id == "b"


def test_trace_replay_uses_recorded_spans(monkeypatch) -> None:
    _reset_app_modules()
    sys.path.insert(0, str(ROOT / "services" / "trace-service"))
    _collector = _load_module(
        "trace_collector",
        ROOT
        / "services"
        / "trace-service"
        / "app"
        / "collector"
        / "trace_collector.py",
    )
    replay = _load_module(
        "replay_engine",
        ROOT / "services" / "trace-service" / "app" / "replay" / "replay_engine.py",
    )
    replay._traces_store.clear()
    replay._traces_store["trace-1"] = [
        {
            "trace_id": "trace-1",
            "span_id": "span-1",
            "service": "retrieval-service",
            "operation": "query",
            "start_time": "2026-01-01T00:00:00Z",
            "attributes": {"query": "refund policy"},
        }
    ]

    result = asyncio.run(replay.replay_trace("trace-1", dry_run=False))

    assert result.status == "replayed"
    assert result.operations[0]["operation"] == "query"
    assert result.operations[0]["replayed"] is True


def test_citation_assembly_uses_stored_document_titles() -> None:
    _reset_app_modules()
    sys.path.insert(0, str(ROOT / "services" / "retrieval-service"))
    index_module = _load_module(
        "app.search.index",
        ROOT / "services" / "retrieval-service" / "app" / "search" / "index.py",
    )
    sys.modules["app.search.index"] = index_module
    assembler = _load_module(
        "citation_assembler",
        ROOT / "services" / "retrieval-service" / "app" / "citation" / "assembler.py",
    )
    index_module.index.clear()
    index_module.index.store_document({"id": "doc-1", "title": "Refund Policy"})
    index_module.index.store_chunk(
        {
            "id": "chunk-1",
            "document_id": "doc-1",
            "content": "Returns are accepted within 30 days of purchase.",
        }
    )

    citations = asyncio.run(
        assembler.assemble_citations(
            assembler.CitationRequest(
                chunk_ids=["chunk-1"], answer="Returns are accepted."
            )
        )
    )

    assert citations[0].document_title == "Refund Policy"
    assert citations[0].document_id == "doc-1"
    assert citations[0].excerpt.startswith("Returns are accepted")


def test_semantic_match_has_deterministic_token_fallback(monkeypatch) -> None:
    _reset_app_modules()
    sys.path.insert(0, str(ROOT / "services" / "eval-service"))
    semantic = _load_module(
        "semantic_match",
        ROOT / "services" / "eval-service" / "app" / "judges" / "semantic_match.py",
    )

    async def empty_embedding(text: str) -> list[float]:
        return []

    monkeypatch.setattr(semantic, "get_embedding", empty_embedding)

    score = asyncio.run(
        semantic.semantic_match_score(
            "Refunds are allowed within 30 days.",
            "Customers may request refunds within 30 days.",
        )
    )

    assert score > 0.4


def test_trace_costs_include_records_users_and_alerts() -> None:
    _reset_app_modules()
    sys.path.insert(0, str(ROOT / "services" / "trace-service"))
    collector = _load_module(
        "app.collector.trace_collector",
        ROOT
        / "services"
        / "trace-service"
        / "app"
        / "collector"
        / "trace_collector.py",
    )
    sys.modules["app.collector.trace_collector"] = collector
    store = _load_module(
        "trace_store",
        ROOT / "services" / "trace-service" / "app" / "storage" / "trace_store.py",
    )
    collector._traces_store.clear()
    collector._traces_store["trace-2"] = [
        {
            "trace_id": "trace-2",
            "span_id": "span-2",
            "service": "retrieval-service",
            "operation": "query",
            "start_time": "2026-01-01T00:00:00Z",
            "end_time": "2026-01-01T00:00:01Z",
            "attributes": {
                "user_id": "user-1",
                "model": "gpt-4o-mini",
                "prompt_tokens": 100,
                "completion_tokens": 20,
                "total_cost_usd": 1.25,
            },
        }
    ]

    costs = asyncio.run(store.get_costs())
    alerts = asyncio.run(store.get_alerts(budget_limit_usd=1.0))

    assert costs["total_usd"] == 1.25
    assert costs["by_user"] == {"user-1": 1.25}
    assert costs["costs"][0]["request_id"] == "trace-2"
    assert alerts["alerts"][0]["type"] == "budget_overrun"


def test_gateway_envelopes_raw_service_lists() -> None:
    _reset_app_modules()
    sys.path.insert(0, str(ROOT / "services" / "api-gateway"))
    proxy = _load_module(
        "app.routes.proxy",
        ROOT / "services" / "api-gateway" / "app" / "routes" / "proxy.py",
    )

    assert proxy._envelope([], "documents") == {"documents": []}
    assert proxy._envelope([{"id": "user-1"}], "users") == {"users": [{"id": "user-1"}]}
    assert proxy._envelope({"users": []}, "users") == {"users": []}


def test_eval_runner_emits_cost_trace(monkeypatch) -> None:
    _reset_app_modules()
    sys.path.insert(0, str(ROOT / "services" / "eval-service"))
    runner = _load_module(
        "app.runners.rag_runner",
        ROOT / "services" / "eval-service" / "app" / "runners" / "rag_runner.py",
    )
    posts: list[dict[str, object]] = []

    class FakeClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        async def __aenter__(self) -> "FakeClient":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def post(self, url: str, json: dict[str, object]) -> None:
            posts.append({"url": url, "json": json})

    monkeypatch.setattr(runner, "AsyncClient", FakeClient)

    asyncio.run(
        runner._emit_eval_trace(
            "run-1",
            "basic",
            1,
            [{"query": "refund policy", "actual": "Returns are allowed."}],
        )
    )

    span = posts[0]["json"]["spans"][0]
    assert posts[0]["url"].endswith("/traces/ingest")
    assert span["service"] == "eval-service"
    assert span["attributes"]["total_cost_usd"] > 0
