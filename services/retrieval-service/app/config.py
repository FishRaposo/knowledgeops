"""Retrieval service configuration."""

from pydantic_settings import BaseSettings


class RetrievalSettings(BaseSettings):
    """Configuration for the Retrieval Service.

    Attributes:
        database_url: PostgreSQL connection string.
        redis_url: Redis connection string.
        llm_gateway_url: LLM Gateway base URL.
        top_k: Default number of results to retrieve.
        rerank_top_k: Number of results after reranking.
        similarity_threshold: Minimum similarity score for valid results.
        trace_service_url: Trace service URL for logging.
        generation_model: LLM model for answer generation.
    """

    database_url: str = "postgresql://knowledgeops:knowledgeops@db:5432/knowledgeops"
    redis_url: str = "redis://redis:6379/0"
    llm_gateway_url: str = "http://llm-gateway:8004"
    top_k: int = 5
    rerank_top_k: int = 3
    similarity_threshold: float = 0.7
    trace_service_url: str = "http://trace-service:8006"
    generation_model: str = "gpt-4o-mini"  # Model for answer generation

    model_config = {"env_file": ".env", "extra": "ignore"}
