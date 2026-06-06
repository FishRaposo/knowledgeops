"""Eval service configuration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "python"))

from shared.config import BaseServiceSettings


class EvalSettings(BaseServiceSettings):
    """Configuration for the Eval Service.

    Inherits common fields from BaseServiceSettings and adds evaluation
    quality thresholds and upstream service URLs.

    Attributes:
        llm_gateway_url: LLM Gateway base URL.
        retrieval_service_url: Retrieval service base URL.
        semantic_threshold: Minimum score for semantic match pass.
        citation_strict: Whether to require exact citation matches.
    """

    llm_gateway_url: str = "http://llm-gateway:8004"
    retrieval_service_url: str = "http://retrieval-service:8003"
    trace_service_url: str = "http://trace-service:8006"
    semantic_threshold: float = 0.8
    citation_strict: bool = True
