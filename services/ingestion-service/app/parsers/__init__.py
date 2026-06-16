"""Document parsers for the Ingestion Service."""

from app.parsers.base import BaseParser
from app.parsers.docx import DocxParser
from app.parsers.html import HtmlParser
from app.parsers.markdown import MarkdownParser
from app.parsers.pdf import PdfParser

PARSERS: dict[str, BaseParser] = {
    ".pdf": PdfParser(),
    ".md": MarkdownParser(),
    ".markdown": MarkdownParser(),
    ".html": HtmlParser(),
    ".htm": HtmlParser(),
    ".docx": DocxParser(),
}

__all__ = [
    "BaseParser",
    "PdfParser",
    "MarkdownParser",
    "HtmlParser",
    "DocxParser",
    "PARSERS",
]
