"""Eval service configuration."""

from shared_core.config import BaseAppConfig


class EvalSettings(BaseAppConfig):
    """Configuration for the Eval Service.

    Inherits common infrastructure fields from ``shared_core.config.BaseAppConfig``
    and adds evaluation quality thresholds and upstream service URLs.
    """

    llm_gateway_url: str = "http://llm-gateway:8004"
    retrieval_service_url: str = "http://retrieval-service:8003"
    trace_service_url: str = "http://trace-service:8006"
    semantic_threshold: float = 0.8
    citation_strict: bool = True
