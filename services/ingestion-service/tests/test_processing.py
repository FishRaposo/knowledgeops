"""Unit tests for ingestion processing: chunking, deduplication, versioning."""

import io

import pytest
from app.parsers.html import HtmlParser
from app.parsers.markdown import MarkdownParser
from app.processing.chunking import chunk_text
from app.processing.deduplication import (
    compute_hash,
    filter_duplicates,
    is_duplicate,
)
from app.processing.versioning import get_next_version, reset_versions

# --- chunking ----------------------------------------------------------------


def test_chunk_text_short_returns_single_chunk() -> None:
    chunks = chunk_text("short text", chunk_size=512, chunk_overlap=64)
    assert len(chunks) == 1
    assert chunks[0].index == 0
    assert chunks[0].content == "short text"
    assert chunks[0].char_count == len("short text")


def test_chunk_text_splits_long_text() -> None:
    text = "sentence. " * 200  # ~2000 chars
    chunks = chunk_text(text, chunk_size=200, chunk_overlap=20)
    assert len(chunks) > 1
    assert all(c.char_count > 0 for c in chunks)
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_chunk_text_prefers_sentence_boundary() -> None:
    text = "First sentence here. " * 30
    chunks = chunk_text(text, chunk_size=120, chunk_overlap=10)
    # Most chunks should end on a sentence boundary when one is available.
    boundary_ends = [c for c in chunks if c.content.endswith(".")]
    assert len(boundary_ends) >= len(chunks) - 1


def test_chunk_text_metadata_offsets() -> None:
    text = "a" * 600
    chunks = chunk_text(text, chunk_size=200, chunk_overlap=0)
    assert chunks[0].metadata["start_char"] == 0
    assert chunks[0].metadata["end_char"] >= 0


# --- deduplication -----------------------------------------------------------


def test_compute_hash_is_sha256_hex() -> None:
    digest = compute_hash("hello")
    assert len(digest) == 64
    assert digest == compute_hash("hello")
    assert digest != compute_hash("world")


def test_is_duplicate() -> None:
    seen = {compute_hash("a")}
    assert is_duplicate("a", seen) is True
    assert is_duplicate("b", seen) is False


def test_filter_duplicates_removes_existing_and_internal() -> None:
    existing = {compute_hash("known")}
    result = filter_duplicates(["known", "new", "new", "fresh"], existing)
    assert result == ["new", "fresh"]


def test_filter_duplicates_empty() -> None:
    assert filter_duplicates([], set()) == []


# --- versioning fallback (in-memory, no DB) ---------------------------------


@pytest.mark.asyncio
async def test_get_next_version_increments_in_memory() -> None:
    reset_versions()
    assert await get_next_version("file.md") == 1
    assert await get_next_version("file.md") == 2
    assert await get_next_version("other.md") == 1
    reset_versions()
    assert await get_next_version("file.md") == 1


# --- parsers -----------------------------------------------------------------


def test_markdown_parser_extracts_title_and_metadata() -> None:
    raw = b"# My Title\n\nSome body text.\n\n## Section\n\nMore."
    result = MarkdownParser().parse(io.BytesIO(raw), "doc.md")
    assert result.title == "My Title"
    assert result.metadata["format"] == "markdown"
    assert result.metadata["heading_count"] >= 1
    assert "My Title" in result.metadata["headings"]


def test_markdown_parser_falls_back_to_filename() -> None:
    result = MarkdownParser().parse(io.BytesIO(b"no heading here"), "plain.md")
    assert result.title == "plain"


def test_html_parser_strips_scripts_and_extracts_title() -> None:
    raw = (
        b"<html><head><title>Page Title</title></head>"
        b"<body><h1>Heading</h1><p>Visible.</p>"
        b"<script>var x=1;</script><style>.a{}</style></body></html>"
    )
    result = HtmlParser().parse(io.BytesIO(raw), "page.html")
    assert result.title == "Page Title"
    assert "Visible." in result.content
    assert "var x" not in result.content
    assert result.metadata["format"] == "html"
    assert "Heading" in result.metadata["headings"]
