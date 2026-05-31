"""Document processing pipeline: chunking, deduplication, versioning."""

from app.processing.chunking import chunk_text
from app.processing.deduplication import compute_hash, is_duplicate
from app.processing.versioning import get_next_version

__all__ = ["chunk_text", "compute_hash", "is_duplicate", "get_next_version"]
