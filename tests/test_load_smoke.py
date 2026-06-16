"""Deterministic load smoke tests for local KnowledgeOps services."""

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


def test_concurrent_keyword_queries_over_realistic_document_volume_are_stable() -> None:
    _reset_app_modules()
    sys.path.insert(0, str(ROOT / "services" / "retrieval-service"))
    hybrid = _load_module(
        "app.search.hybrid",
        ROOT / "services" / "retrieval-service" / "app" / "search" / "hybrid.py",
    )
    hybrid.index.clear()
    for doc_idx in range(20):
        doc_id = f"doc-{doc_idx}"
        title = "Refund Policy" if doc_idx == 7 else f"Policy {doc_idx}"
        hybrid.index.store_document({"id": doc_id, "title": title})
        for chunk_idx in range(10):
            content = (
                "Refund policy allows returns within 30 days."
                if doc_idx == 7 and chunk_idx == 3
                else f"Operational note {doc_idx}-{chunk_idx} for internal knowledge base load testing."
            )
            hybrid.index.store_chunk(
                {
                    "id": f"chunk-{doc_idx}-{chunk_idx}",
                    "document_id": doc_id,
                    "content": content,
                    "metadata": {"title": title},
                }
            )

    async def run_many() -> list[object]:
        return await asyncio.gather(
            *[
                hybrid.search(hybrid.SearchRequest(query="refund policy", top_k=1))
                for _ in range(25)
            ]
        )

    responses = asyncio.run(run_many())

    assert len(responses) == 25
    assert hybrid.index.chunk_count == 200
    assert all(response.results[0].chunk_id == "chunk-7-3" for response in responses)
