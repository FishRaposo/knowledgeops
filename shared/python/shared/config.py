"""Base configuration for all KnowledgeOps services."""

from pydantic_settings import BaseSettings


class BaseServiceSettings(BaseSettings):
    """Base settings class shared across all Python services.

    Each service should subclass this and add service-specific settings.

    Attributes:
        database_url: PostgreSQL connection string.
        redis_url: Redis connection string.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
        log_format: Logging format (json or text).
        environment: Deployment environment (development, staging, production).
    """

    database_url: str = "postgresql://knowledgeops:knowledgeops@db:5432/knowledgeops"
    redis_url: str = "redis://redis:6379/0"
    log_level: str = "INFO"
    log_format: str = "json"
    environment: str = "development"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


MODEL_PRICING = {
    "gpt-4o": {"prompt": 0.000005, "completion": 0.000015},
    "gpt-4o-mini": {"prompt": 0.00000015, "completion": 0.0000006},
    "text-embedding-3-small": {"prompt": 0.00000002, "completion": 0.0},
    "gpt-4-turbo": {"prompt": 0.00001, "completion": 0.00003},
    "gpt-3.5-turbo": {"prompt": 0.0000005, "completion": 0.0000015},
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Estimate request cost in USD using model-specific token rates."""
    pricing = MODEL_PRICING.get(model, {"prompt": 0.00001, "completion": 0.00003})
    cost = (prompt_tokens * pricing["prompt"]) + (completion_tokens * pricing["completion"])
    return round(cost, 6)
