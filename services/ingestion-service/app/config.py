"""Ingestion service configuration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "python"))

from shared.config import BaseServiceSettings


class IngestionSettings(BaseServiceSettings):
    """Configuration for the Ingestion Service.

    Inherits common fields from BaseServiceSettings and adds ingestion
    chunking parameters and upstream service URLs.

    Attributes:
        llm_gateway_url: LLM Gateway base URL for embeddings.
        chunk_size: Target chunk size in characters.
        chunk_overlap: Overlap between chunks in characters.
        max_file_size_mb: Maximum upload file size in megabytes.
    """

    llm_gateway_url: str = "http://llm-gateway:8004"
    chunk_size: int = 512
    chunk_overlap: int = 64
    max_file_size_mb: int = 50
