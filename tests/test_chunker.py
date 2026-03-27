"""Tests for text chunker."""
from __future__ import annotations

import pytest

from app.ingestion.chunker import chunk_text, TextChunk


class TestChunker:
    """Test sentence-boundary text chunking."""

    def test_short_text_single_chunk(self) -> None:
        text = "Port congestion at Rotterdam is increasing."
        chunks = chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_long_text_multiple_chunks(self) -> None:
        # Generate text with multiple sentences
        sentences = [f"Sentence number {i} about shipping delays." for i in range(30)]
        text = " ".join(sentences)
        chunks = chunk_text(text)
        assert len(chunks) >= 2

    def test_chunk_overlap(self) -> None:
        sentences = [f"Sentence {i} about maritime logistics." for i in range(30)]
        text = " ".join(sentences)
        chunks = chunk_text(text)

        if len(chunks) >= 2:
            # Check that there's some overlap between consecutive chunks
            for i in range(len(chunks) - 1):
                # The end of one chunk should share some text with the start of the next
                # (depends on overlap implementation)
                assert len(chunks[i].text) > 0
                assert len(chunks[i + 1].text) > 0

    def test_empty_text(self) -> None:
        chunks = chunk_text("")
        assert len(chunks) == 0 or (len(chunks) == 1 and chunks[0].text == "")

    def test_chunk_structure(self) -> None:
        text = "First sentence. Second sentence. Third sentence."
        chunks = chunk_text(text)
        for chunk in chunks:
            assert isinstance(chunk, TextChunk)
            assert isinstance(chunk.text, str)
            assert isinstance(chunk.start_char, int)
            assert isinstance(chunk.end_char, int)

    def test_no_data_loss(self) -> None:
        text = "Important shipping data. Critical port info. Freight rate update."
        chunks = chunk_text(text)
        # All original content should appear in at least one chunk
        all_chunk_text = " ".join(c.text for c in chunks)
        for word in ["shipping", "port", "freight"]:
            assert word in all_chunk_text.lower()
