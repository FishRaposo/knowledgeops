"""Base parser interface for document text extraction."""

from abc import ABC, abstractmethod
from typing import BinaryIO

from pydantic import BaseModel, Field


class ParseResult(BaseModel):
    """Result of parsing a document.

    Attributes:
        title: Extracted document title.
        content: Extracted raw text content.
        metadata: Parser-specific metadata (page count, sections, etc.).
    """

    title: str = Field(description="Extracted document title")
    content: str = Field(description="Raw extracted text content")
    metadata: dict[str, object] = Field(
        default_factory=dict, description="Parser metadata"
    )


class BaseParser(ABC):
    """Abstract base class for document parsers.

    Each parser handles a specific file format and extracts raw text content.
    """

    @abstractmethod
    def parse(self, file: BinaryIO, filename: str) -> ParseResult:
        """Parse a document file and extract text content.

        Args:
            file: File-like object to parse.
            filename: Original filename for extension detection.

        Returns:
            ParseResult with extracted title, content, and metadata.
        """
        ...
