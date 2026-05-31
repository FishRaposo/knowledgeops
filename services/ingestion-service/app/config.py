"""Ingestion service configuration."""

from pydantic_settings import BaseSettings


class IngestionSettings(BaseSettings):
    """Configuration for the Ingestion Service.

    Attributes:
        database_url: PostgreSQL connection string.
        redis_url: Redis connection string.
        llm_gateway_url: LLM Gateway base URL for embeddings.
        chunk_size: Target chunk size in characters.
        chunk_overlap: Overlap between chunks in characters.
        max_file_size_mb: Maximum upload file size in megabytes.
    """

    database_url: str = "postgresql://knowledgeops:knowledgeops@db:5432/knowledgeops"
    redis_url: str = "redis://redis:6379/0"
    llm_gateway_url: str = "http://llm-gateway:8004"
    chunk_size: int = 512
    chunk_overlap: int = 64
    max_file_size_mb: int = 50

    model_config = {"env_file": ".env", "extra": "ignore"}
