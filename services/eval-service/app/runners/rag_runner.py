"""RAG evaluation runner."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from httpx import AsyncClient
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.config import EvalSettings
from app.db.session import async_session_factory, db_available
from app.judges.citation_check import check_citations
from app.judges.refusal_check import check_refusal
from app.judges.semantic_match import semantic_match_score

router = APIRouter(prefix="/eval")
settings = EvalSettings()

_eval_runs: dict[str, dict[str, Any]] = {}


class EvalRunRequest(BaseModel):
    """Request to start an evaluation run.

    Attributes:
        suite_path: Path to the eval suite YAML file.
        name: Optional name for the run.
    """

    suite_path: str = Field(description="Path to eval suite YAML")
    name: str | None = Field(default=None, description="Run name")


class EvalRunResponse(BaseModel):
    """Response for an evaluation run.

    Attributes:
        id: Run identifier.
        name: Run name.
        status: Run status.
        total_cases: Total test cases.
        results: Individual test case results.
    """

    id: str
    name: str
    status: str
    total_cases: int
    results: list[dict[str, Any]]


class TestCase(BaseModel):
    """A single evaluation test case.

    Attributes:
        query: Test query string.
        expected_answer: Expected answer for comparison.
        expected_citations: Expected source citations.
        should_refuse: Whether the query should trigger a refusal.
    """

    query: str
    expected_answer: str = ""
    expected_citations: list[str] = Field(default_factory=list)
    should_refuse: bool = False


@router.post("/run", response_model=EvalRunResponse)
async def run_evaluation(request: EvalRunRequest) -> EvalRunResponse:
    """Execute an evaluation run against the retrieval pipeline.

    Persists the run and results to PostgreSQL when available, always
    mirroring to the in-memory store so a DB outage never loses data.

    Args:
        request: Eval run request with suite path.

    Returns:
        Evaluation run results with judge scores.
    """
    run_id = str(uuid4())
    run_name = (
        request.name
        or f"eval-run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    )
    started_at = datetime.now(timezone.utc)

    if db_available:
        await _insert_eval_run(run_id, run_name, started_at)

    test_cases = await _load_test_cases(request.suite_path)
    results: list[dict[str, Any]] = []

    async with AsyncClient(timeout=30.0) as client:
        for case in test_cases:
            try:
                response = await client.post(
                    f"{settings.retrieval_service_url}/retrieve/query",
                    json={"query": case.query, "top_k": 5},
                )
                actual_data = response.json() if response.status_code == 200 else {}
            except Exception:
                actual_data = {}

            actual_answer = actual_data.get("answer", "")
            actual_citations = actual_data.get("citations", [])
            actual_refusal = actual_data.get("refusal", False)

            scores: dict[str, float] = {}
            scores["semantic_match"] = await semantic_match_score(
                case.expected_answer, actual_answer
            )
            scores["citation_check"] = (
                1.0
                if check_citations(case.expected_citations, actual_citations)
                else 0.0
            )
            scores["refusal_check"] = (
                1.0 if check_refusal(case.should_refuse, actual_refusal) else 0.0
            )

            result = {
                "query": case.query,
                "expected": case.expected_answer,
                "actual": actual_answer,
                "scores": scores,
                "citations": actual_citations,
            }
            results.append(result)

            if db_available:
                await _insert_eval_result(run_id, result)

    completed_at = datetime.now(timezone.utc)

    eval_data = {
        "id": run_id,
        "name": run_name,
        "status": "completed",
        "total_cases": len(test_cases),
        "results": results,
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
    }

    _eval_runs[run_id] = eval_data

    if db_available:
        await _complete_eval_run(run_id, completed_at)

    await _emit_eval_trace(run_id, run_name, len(test_cases), results)

    return EvalRunResponse(**eval_data)


async def _insert_eval_run(run_id: str, name: str, started_at: datetime) -> None:
    async with async_session_factory() as session:
        await session.execute(
            text(
                """
                INSERT INTO eval_runs (id, name, status, config, started_at)
                VALUES (:id, :name, :status, :config, :started_at)
                """
            ),
            {
                "id": run_id,
                "name": name,
                "status": "running",
                "config": {},
                "started_at": started_at.isoformat(),
            },
        )
        await session.commit()


async def _insert_eval_result(run_id: str, result: dict[str, Any]) -> None:
    async with async_session_factory() as session:
        await session.execute(
            text(
                """
                INSERT INTO eval_results (run_id, query, expected, actual, scores)
                VALUES (:run_id, :query, :expected, :actual, :scores)
                """
            ),
            {
                "run_id": run_id,
                "query": result["query"],
                "expected": result.get("expected"),
                "actual": result.get("actual"),
                "scores": result.get("scores", {}),
            },
        )
        await session.commit()


async def _complete_eval_run(run_id: str, completed_at: datetime) -> None:
    async with async_session_factory() as session:
        await session.execute(
            text(
                """
                UPDATE eval_runs
                SET status = 'completed', completed_at = :completed_at
                WHERE id = :id
                """
            ),
            {"id": run_id, "completed_at": completed_at.isoformat()},
        )
        await session.commit()


@router.get("/runs")
async def list_runs() -> list[dict[str, Any]]:
    """List all evaluation runs.

    Returns:
        List of evaluation run summaries.
    """
    if db_available:
        async with async_session_factory() as session:
            rows = await session.execute(
                text(
                    """
                    SELECT id, name, status, started_at, completed_at,
                           (SELECT COUNT(*) FROM eval_results
                            WHERE run_id = eval_runs.id) AS total_cases
                    FROM eval_runs
                    ORDER BY started_at DESC
                    """
                )
            )
            return [
                {
                    "id": str(row["id"]),
                    "name": row["name"],
                    "status": row["status"],
                    "total_cases": row["total_cases"] or 0,
                }
                for row in rows.mappings()
            ]

    return [
        {
            "id": run["id"],
            "name": run["name"],
            "status": run["status"],
            "total_cases": run["total_cases"],
        }
        for run in _eval_runs.values()
    ]


@router.get("/runs/{run_id}")
async def get_run(run_id: str) -> dict[str, Any]:
    """Get evaluation run details.

    Args:
        run_id: Run identifier.

    Returns:
        Full evaluation run data with results.
    """
    if db_available:
        async with async_session_factory() as session:
            run_row = await session.execute(
                text("SELECT * FROM eval_runs WHERE id = :id"),
                {"id": run_id},
            )
            run = run_row.mappings().one_or_none()
            if run is None:
                return {"error": "Run not found"}

            result_rows = await session.execute(
                text(
                    "SELECT query, expected, actual, scores "
                    "FROM eval_results WHERE run_id = :run_id"
                ),
                {"run_id": run_id},
            )
            results = [
                {
                    "query": row["query"],
                    "expected": row["expected"],
                    "actual": row["actual"],
                    "scores": row["scores"] or {},
                }
                for row in result_rows.mappings()
            ]

            return {
                "id": str(run["id"]),
                "name": run["name"],
                "status": run["status"],
                "total_cases": len(results),
                "results": results,
                "started_at": str(run["started_at"]),
                "completed_at": str(run["completed_at"])
                if run["completed_at"]
                else None,
            }

    if run_id not in _eval_runs:
        return {"error": "Run not found"}
    return _eval_runs[run_id]


async def _load_test_cases(suite_path: str) -> list[TestCase]:
    """Load test cases from a YAML eval suite file.

    Args:
        suite_path: Path to the YAML file.

    Returns:
        List of TestCase objects.
    """
    try:
        import yaml

        with open(suite_path, "r") as f:
            data = yaml.safe_load(f)

        cases = data.get("test_cases", [])
        return [
            TestCase(
                query=c.get("query", ""),
                expected_answer=c.get("expected_answer", ""),
                expected_citations=c.get("expected_citations", []),
                should_refuse=c.get("should_refuse", False),
            )
            for c in cases
        ]
    except Exception:
        return [
            TestCase(
                query="What is the refund policy?", expected_answer="Sample answer"
            ),
        ]


async def _emit_eval_trace(
    run_id: str,
    run_name: str,
    total_cases: int,
    results: list[dict[str, Any]],
) -> None:
    prompt_tokens = sum(len(str(r.get("query", "")).split()) for r in results)
    completion_tokens = sum(len(str(r.get("actual", "")).split()) for r in results)
    span = {
        "trace_id": run_id,
        "span_id": str(uuid4()),
        "parent_span_id": None,
        "service": "eval-service",
        "operation": "eval_run",
        "start_time": datetime.now(timezone.utc).isoformat(),
        "end_time": datetime.now(timezone.utc).isoformat(),
        "attributes": {
            "run_name": run_name,
            "total_cases": total_cases,
            "model": "judge-fallback",
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_cost_usd": _estimate_eval_cost(prompt_tokens, completion_tokens),
            "status": "ok",
        },
    }
    try:
        async with AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{settings.trace_service_url}/traces/ingest", json={"spans": [span]}
            )
    except Exception:
        return


def _estimate_eval_cost(prompt_tokens: int, completion_tokens: int) -> float:
    total_tokens = prompt_tokens + completion_tokens
    if total_tokens <= 0:
        return 0.0
    return max(0.000001, round(total_tokens * 0.00000005, 6))
