"""Text chunking with configurable size and overlap."""

from pydantic import BaseModel, Field

from app.config import IngestionSettings

settings = IngestionSettings()


class TextChunk(BaseModel):
    """A chunk of text extracted from a document.

    Attributes:
        content: Chunk text content.
        index: Position within the document.
        char_count: Character count of the chunk.
        metadata: Chunk-level metadata.
    """

    content: str = Field(description="Chunk text content")
    index: int = Field(description="Position within the document")
    char_count: int = Field(description="Character count")
    metadata: dict[str, object] = Field(default_factory=dict, description="Chunk metadata")


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[TextChunk]:
    """Split text into overlapping chunks.

    Uses a sliding window approach with configurable size and overlap.
    Chunks are split at sentence boundaries when possible.

    Args:
        text: Raw text to chunk.
        chunk_size: Target chunk size in characters (defaults to config).
        chunk_overlap: Overlap between chunks in characters (defaults to config).

    Returns:
        List of TextChunk objects with content and position info.
    """
    size = chunk_size or settings.chunk_size
    overlap = chunk_overlap or settings.chunk_overlap

    if len(text) <= size:
        return [TextChunk(content=text, index=0, char_count=len(text))]

    chunks: list[TextChunk] = []
    start = 0
    idx = 0

    while start < len(text):
        end = start + size
        chunk_content = text[start:end]

        if end < len(text):
            last_period = chunk_content.rfind(".")
            last_newline = chunk_content.rfind("\n")
            split_point = max(last_period, last_newline)
            if split_point > size // 2:
                chunk_content = text[start : start + split_point + 1]
                end = start + split_point + 1

        chunk_content = chunk_content.strip()
        if chunk_content:
            chunks.append(
                TextChunk(
                    content=chunk_content,
                    index=idx,
                    char_count=len(chunk_content),
                    metadata={"start_char": start, "end_char": start + len(chunk_content)},
                )
            )
            idx += 1

        start = end - overlap
        if start <= chunks[-1].metadata.get("start_char", 0) if chunks else True:
            start = end

    return chunks
