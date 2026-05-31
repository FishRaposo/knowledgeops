"""Eval service configuration."""

from pydantic_settings import BaseSettings


class EvalSettings(BaseSettings):
    """Configuration for the Eval Service.

    Attributes:
        database_url: PostgreSQL connection string.
        llm_gateway_url: LLM Gateway base URL.
        retrieval_service_url: Retrieval service base URL.
        semantic_threshold: Minimum score for semantic match pass.
        citation_strict: Whether to require exact citation matches.
    """

    database_url: str = "postgresql://knowledgeops:knowledgeops@db:5432/knowledgeops"
    llm_gateway_url: str = "http://llm-gateway:8004"
    retrieval_service_url: str = "http://retrieval-service:8003"
    trace_service_url: str = "http://trace-service:8006"
    semantic_threshold: float = 0.8
    citation_strict: bool = True

    model_config = {"env_file": ".env", "extra": "ignore"}
