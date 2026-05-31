"""PDF document parser using PyMuPDF."""

from typing import BinaryIO

import fitz

from app.parsers.base import BaseParser, ParseResult


class PdfParser(BaseParser):
    """Parser for PDF documents using PyMuPDF (fitz).

    Extracts text from all pages, handling multi-column and formatted PDFs.
    """

    def parse(self, file: BinaryIO, filename: str) -> ParseResult:
        """Parse a PDF file and extract text from all pages.

        Args:
            file: PDF file binary stream.
            filename: Original filename.

        Returns:
            ParseResult with text from all pages and page count metadata.
        """
        doc = fitz.open(stream=file.read(), filetype="pdf")
        pages: list[str] = []
        for page in doc:
            pages.append(page.get_text())

        content = "\n\n".join(pages)
        title = filename.rsplit(".", 1)[0] if "." in filename else filename

        return ParseResult(
            title=title,
            content=content,
            metadata={
                "page_count": len(pages),
                "format": "pdf",
                "char_count": len(content),
            },
        )
