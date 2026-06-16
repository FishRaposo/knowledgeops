"""KnowledgeOps shared domain models.

Infrastructure (config, logging, database, health) is provided by ``shared_core``;
this package now holds only the cross-service domain DTOs. Generic span/cost DTOs
also live in ``shared_core.tracing`` (``TraceSpan``, ``CostRecord``) for new code.
"""

from shared.models import (
    Chunk,
    Citation,
    CostRecord,
    Document,
    DocumentStatus,
    EvalResult,
    EvalRun,
    QueryRequest,
    QueryResponse,
    TraceSpan,
    User,
)

__all__ = [
    "Chunk",
    "Citation",
    "CostRecord",
    "Document",
    "DocumentStatus",
    "EvalResult",
    "EvalRun",
    "QueryRequest",
    "QueryResponse",
    "TraceSpan",
    "User",
]
