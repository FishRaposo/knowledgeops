"""Markdown document parser."""

from typing import BinaryIO

from markdown_it import MarkdownIt

from app.parsers.base import BaseParser, ParseResult


class MarkdownParser(BaseParser):
    """Parser for Markdown documents.

    Converts Markdown to plain text, extracting headings as structure.
    """

    def parse(self, file: BinaryIO, filename: str) -> ParseResult:
        """Parse a Markdown file and extract text content.

        Args:
            file: Markdown file binary stream.
            filename: Original filename.

        Returns:
            ParseResult with extracted text and heading structure metadata.
        """
        raw = file.read().decode("utf-8")
        md = MarkdownIt()
        tokens = md.parse(raw)

        text_parts: list[str] = []
        headings: list[str] = []

        for token in tokens:
            if token.type == "heading_open":
                pass
            elif token.type == "inline":
                text_parts.append(token.content)
            elif token.type == "heading_close":
                if text_parts:
                    headings.append(text_parts[-1])

        title = headings[0] if headings else filename.rsplit(".", 1)[0]
        content = raw

        return ParseResult(
            title=title,
            content=content,
            metadata={
                "format": "markdown",
                "heading_count": len(headings),
                "headings": headings,
                "char_count": len(content),
            },
        )
