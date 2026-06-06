"""Trace service configuration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "python"))

from shared.config import BaseServiceSettings


class TraceSettings(BaseServiceSettings):
    """Configuration for the Trace Service.

    Inherits common fields (database_url, redis_url, log_level) from
    BaseServiceSettings and adds trace-specific settings.

    Attributes:
        budget_alert_limit_usd: Cost threshold for budget alerts.
        retrieval_service_url: URL for the retrieval service.
    """

    budget_alert_limit_usd: float = 100.0
    retrieval_service_url: str = "http://retrieval-service:8003"
