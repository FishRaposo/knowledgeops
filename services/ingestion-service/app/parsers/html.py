"""HTML document parser using BeautifulSoup4."""

from typing import BinaryIO

from bs4 import BeautifulSoup

from app.parsers.base import BaseParser, ParseResult


class HtmlParser(BaseParser):
    """Parser for HTML documents using BeautifulSoup4.

    Extracts visible text content, handling tags, scripts, and styles.
    """

    def parse(self, file: BinaryIO, filename: str) -> ParseResult:
        """Parse an HTML file and extract visible text.

        Args:
            file: HTML file binary stream.
            filename: Original filename.

        Returns:
            ParseResult with visible text and structural metadata.
        """
        raw = file.read().decode("utf-8")
        soup = BeautifulSoup(raw, "html.parser")

        for element in soup(["script", "style", "nav", "footer"]):
            element.decompose()

        title_tag = soup.find("title")
        title = (
            title_tag.get_text().strip() if title_tag else filename.rsplit(".", 1)[0]
        )

        content = soup.get_text(separator="\n", strip=True)

        headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])]

        return ParseResult(
            title=title,
            content=content,
            metadata={
                "format": "html",
                "heading_count": len(headings),
                "headings": headings,
                "char_count": len(content),
            },
        )
