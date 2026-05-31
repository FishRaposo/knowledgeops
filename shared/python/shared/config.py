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
