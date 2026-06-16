"""KnowledgeOps platform demo — exercises the shared-core capabilities the services use.

Runs fully offline (no database, Redis, or LLM keys required) to demonstrate the
ingestion -> retrieval -> evaluation -> cost-tracking wiring that the eight services
compose at runtime.
"""

import asyncio

from loguru import logger
from shared_core.docparse import ChunkStrategy, chunk_text, compute_hash, get_parser
from shared_core.embeddings import cosine_similarity, get_embedding_provider
from shared_core.evaljudge import CitationJudge, RefusalJudge, SemanticMatchJudge
from shared_core.logging import setup_logging
from shared_core.pricing import calculate_cost

SAMPLE_DOC = b"""# Refund Policy

Customers may request a refund within 30 days of purchase. Refunds are issued
to the original payment method within 5 business days. Digital goods are
non-refundable once downloaded.
"""


async def main() -> None:
    setup_logging(level="INFO", service_name="knowledgeops-demo")
    logger.info("=== KnowledgeOps platform demo (offline) ===")

    # 1. Ingestion: parse + chunk + content-hash (shared_core.docparse)
    parser = get_parser("refund_policy.md")
    doc = parser.parse(SAMPLE_DOC, filename="refund_policy.md")
    chunks = chunk_text(doc.text, strategy=ChunkStrategy.STRUCTURAL, chunk_size=200)
    logger.info(
        "Ingested '{}' -> {} chunk(s); content hash {}",
        doc.title,
        len(chunks),
        compute_hash(doc.text)[:12],
    )

    # 2. Retrieval: embed query + chunks, rank by cosine (shared_core.embeddings)
    provider = get_embedding_provider(offline=True)
    query = "How long do I have to request a refund?"
    q_vec = (await provider.embed(query)).vector
    scored = []
    for chunk in chunks:
        c_vec = (await provider.embed(chunk)).vector
        scored.append((cosine_similarity(q_vec, c_vec), chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    top_score, top_chunk = scored[0]
    logger.info(
        "Top retrieved chunk (score {:.3f}): {}",
        top_score,
        top_chunk[:60].replace("\n", " "),
    )

    # 3. Grounded answer with a citation marker
    answer = "Refunds may be requested within 30 days of purchase [1]."

    # 4. Cost tracking (shared_core.pricing)
    cost = calculate_cost("gpt-4o-mini", prompt_tokens=320, completion_tokens=48)
    logger.info("Estimated LLM cost for the answer: ${:.6f}", cost)

    # 5. Evaluation (shared_core.evaljudge)
    semantic = await SemanticMatchJudge(threshold=0.2).evaluate(
        expected="You can request a refund within 30 days.", actual=answer
    )
    citation = await CitationJudge().evaluate(expected=None, actual=answer)
    refusal = await RefusalJudge().evaluate(expected=None, actual=answer)
    logger.info(
        "Eval — semantic_match: {} (score {:.2f}) | citation: {} | refused: {}",
        semantic.passed,
        semantic.score,
        citation.passed,
        refusal.passed,
    )

    logger.info(
        "=== Demo complete: ingestion -> retrieval -> answer -> cost -> eval ==="
    )


if __name__ == "__main__":
    asyncio.run(main())
