"""Gateway service configuration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "python"))

from shared.config import BaseServiceSettings


class GatewaySettings(BaseServiceSettings):
    """Configuration for the API Gateway.

    Inherits common fields from BaseServiceSettings and adds service URL
    routing and gateway-specific settings.

    Attributes:
        auth_service_url: Base URL for the Auth Service.
        ingestion_service_url: Base URL for the Ingestion Service.
        retrieval_service_url: Base URL for the Retrieval Service.
        eval_service_url: Base URL for the Eval Service.
        trace_service_url: Base URL for the Trace Service.
        llm_gateway_url: Base URL for the LLM Gateway.
    """

    auth_service_url: str = "http://auth-service:8001"
    ingestion_service_url: str = "http://ingestion-service:8002"
    retrieval_service_url: str = "http://retrieval-service:8003"
    eval_service_url: str = "http://eval-service:8005"
    trace_service_url: str = "http://trace-service:8006"
    llm_gateway_url: str = "http://llm-gateway:8004"
    allow_dev_auth: bool = False
    demo_token: str = "dev-admin-token"
    cost_budget_limit_usd: float = 100.0
    cors_allow_origins: list[str] = ["*"]
