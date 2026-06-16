"""Retrieval service configuration."""

from shared_core.config import BaseAppConfig


class RetrievalSettings(BaseAppConfig):
    """Configuration for the Retrieval Service.

    Inherits common infrastructure fields from ``shared_core.config.BaseAppConfig``
    and adds retrieval quality parameters and upstream service URLs.
    """

    llm_gateway_url: str = "http://llm-gateway:8004"
    top_k: int = 5
    rerank_top_k: int = 3
    similarity_threshold: float = 0.7
    trace_service_url: str = "http://trace-service:8006"
    generation_model: str = "gpt-4o-mini"
