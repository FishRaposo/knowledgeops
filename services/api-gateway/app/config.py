"""Gateway service configuration."""

from shared_core.config import BaseAppConfig


class GatewaySettings(BaseAppConfig):
    """Configuration for the API Gateway.

    Inherits common infrastructure fields (DATABASE_URL, REDIS_URL, LOG_LEVEL, ...)
    from ``shared_core.config.BaseAppConfig`` and adds service-URL routing and
    gateway-specific settings.
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
