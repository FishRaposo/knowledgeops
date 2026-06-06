"""Retrieval service configuration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "python"))

from shared.config import BaseServiceSettings


class RetrievalSettings(BaseServiceSettings):
    """Configuration for the Retrieval Service.

    Inherits common fields from BaseServiceSettings and adds retrieval
    quality parameters and upstream service URLs.

    Attributes:
        llm_gateway_url: LLM Gateway base URL.
        top_k: Default number of results to retrieve.
        rerank_top_k: Number of results after reranking.
        similarity_threshold: Minimum similarity score for valid results.
        trace_service_url: Trace service URL for logging.
        generation_model: LLM model for answer generation.
    """

    llm_gateway_url: str = "http://llm-gateway:8004"
    top_k: int = 5
    rerank_top_k: int = 3
    similarity_threshold: float = 0.7
    trace_service_url: str = "http://trace-service:8006"
    generation_model: str = "gpt-4o-mini"
