"""Trace service configuration."""

from shared_core.config import BaseAppConfig


class TraceSettings(BaseAppConfig):
    """Configuration for the Trace Service.

    Inherits common infrastructure fields (DATABASE_URL, REDIS_URL, LOG_LEVEL)
    from ``shared_core.config.BaseAppConfig`` and adds trace-specific settings.
    """

    budget_alert_limit_usd: float = 100.0
    retrieval_service_url: str = "http://retrieval-service:8003"
