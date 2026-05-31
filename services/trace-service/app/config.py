"""Trace service configuration."""

from pydantic_settings import BaseSettings


class TraceSettings(BaseSettings):
    """Configuration for the Trace Service.

    Attributes:
        database_url: PostgreSQL connection string.
    """

    database_url: str = "postgresql://knowledgeops:knowledgeops@db:5432/knowledgeops"
    budget_alert_limit_usd: float = 100.0

    model_config = {"env_file": ".env", "extra": "ignore"}
