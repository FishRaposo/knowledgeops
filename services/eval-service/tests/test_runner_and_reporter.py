"""Tests for the eval runner, markdown reporter, and suite loading."""

from typing import Any

import pytest
from app.reporters.markdown import generate_markdown_report
from app.runners import rag_runner
from httpx import AsyncClient


@pytest.fixture(autouse=True)
def _clear_runs() -> None:
    rag_runner._eval_runs.clear()
    yield
    rag_runner._eval_runs.clear()


# --- markdown reporter -------------------------------------------------------


def test_generate_markdown_report_with_results() -> None:
    run_data = {
        "name": "My Run",
        "status": "completed",
        "results": [
            {
                "query": "What is the refund policy?",
                "scores": {
                    "semantic_match": 0.9,
                    "citation_check": 1.0,
                    "refusal_check": 1.0,
                },
            }
        ],
    }
    report = generate_markdown_report(run_data)
    assert "# Evaluation Report: My Run" in report
    assert "Total test cases:** 1" in report
    assert "| Query | Semantic | Citation | Refusal |" in report
    assert "KnowledgeOps Eval Service" in report


def test_generate_markdown_report_empty() -> None:
    report = generate_markdown_report({"name": "Empty", "status": "completed"})
    assert "Total test cases:** 0" in report
    assert "| Query |" not in report


@pytest.mark.asyncio
async def test_report_endpoint_404_for_unknown_run(client: AsyncClient) -> None:
    resp = await client.get("/eval/runs/does-not-exist/report")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_report_endpoint_returns_markdown(client: AsyncClient) -> None:
    rag_runner._eval_runs["r1"] = {
        "id": "r1",
        "name": "Stored",
        "status": "completed",
        "results": [],
    }
    resp = await client.get("/eval/runs/r1/report")
    assert resp.status_code == 200
    assert "Stored" in resp.json()["report"]


@pytest.mark.asyncio
async def test_report_endpoint_falls_back_to_db(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Run is absent from the in-memory store (e.g. after a restart) but lives
    # in the DB; the report endpoint must load it via the DB fallback.
    from app.db import session as db_session
    from app.reporters import markdown as reporter

    async def _fake_get_run(run_id: str) -> dict[str, Any]:
        assert run_id == "persisted"
        return {
            "id": "persisted",
            "name": "FromDB",
            "status": "completed",
            "results": [],
        }

    monkeypatch.setattr(db_session, "db_available", True)
    monkeypatch.setattr(reporter, "get_run", _fake_get_run)

    resp = await client.get("/eval/runs/persisted/report")
    assert resp.status_code == 200
    assert "FromDB" in resp.json()["report"]


@pytest.mark.asyncio
async def test_report_endpoint_404_when_db_lacks_run(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.db import session as db_session
    from app.reporters import markdown as reporter

    async def _fake_get_run(run_id: str) -> dict[str, Any]:
        return {"error": "Run not found"}

    monkeypatch.setattr(db_session, "db_available", True)
    monkeypatch.setattr(reporter, "get_run", _fake_get_run)

    resp = await client.get("/eval/runs/missing/report")
    assert resp.status_code == 404


# --- suite loading -----------------------------------------------------------


@pytest.mark.asyncio
async def test_load_test_cases_from_yaml(tmp_path: Any) -> None:
    suite = tmp_path / "suite.yaml"
    suite.write_text(
        "test_cases:\n"
        "  - query: What is X?\n"
        "    expected_answer: X is a thing\n"
        "    expected_citations: [doc-a]\n"
        "    should_refuse: false\n"
    )
    cases = await rag_runner._load_test_cases(str(suite))
    assert len(cases) == 1
    assert cases[0].query == "What is X?"
    assert cases[0].expected_citations == ["doc-a"]


@pytest.mark.asyncio
async def test_load_test_cases_missing_file_uses_default() -> None:
    cases = await rag_runner._load_test_cases("/nonexistent/suite.yaml")
    assert len(cases) >= 1
    assert cases[0].query


# --- run_evaluation end-to-end (retrieval + trace mocked) -------------------


@pytest.mark.asyncio
async def test_run_evaluation_scores_cases(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    suite = tmp_path / "suite.yaml"
    suite.write_text(
        "test_cases:\n"
        "  - query: refund?\n"
        "    expected_answer: refund within 30 days\n"
        "    should_refuse: false\n"
    )

    class _Resp:
        status_code = 200

        def json(self) -> dict[str, Any]:
            return {
                "answer": "refund within 30 days",
                "citations": [{"document_title": "Policy"}],
                "refusal": False,
            }

    class _MockClient:
        def __init__(self, *a: Any, **k: Any) -> None: ...
        async def __aenter__(self) -> "_MockClient":
            return self

        async def __aexit__(self, *a: Any) -> None: ...
        async def post(self, url: str, *a: Any, **k: Any) -> _Resp:
            return _Resp()

    # Mock both the retrieval call and the trace emission.
    monkeypatch.setattr(rag_runner, "AsyncClient", _MockClient)

    async def _no_embedding(_text: str) -> list[float]:
        return []

    monkeypatch.setattr("app.judges.semantic_match.get_embedding", _no_embedding)

    resp = await client.post("/eval/run", json={"suite_path": str(suite), "name": "ci"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"
    assert body["total_cases"] == 1
    scores = body["results"][0]["scores"]
    assert scores["refusal_check"] == 1.0
    assert scores["semantic_match"] == 1.0  # exact lexical match


@pytest.mark.asyncio
async def test_list_runs_after_run(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    rag_runner._eval_runs["r2"] = {
        "id": "r2",
        "name": "n",
        "status": "completed",
        "total_cases": 3,
    }
    resp = await client.get("/eval/runs")
    assert resp.status_code == 200
    assert any(r["id"] == "r2" for r in resp.json())
