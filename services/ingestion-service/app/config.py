"""Ingestion service configuration."""

from shared_core.config import BaseAppConfig


class IngestionSettings(BaseAppConfig):
    """Configuration for the Ingestion Service.

    Inherits common infrastructure fields from ``shared_core.config.BaseAppConfig``
    and adds ingestion chunking parameters and upstream service URLs.
    """

    llm_gateway_url: str = "http://llm-gateway:8004"
    chunk_size: int = 512
    chunk_overlap: int = 64
    max_file_size_mb: int = 50
