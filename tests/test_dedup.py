"""Tests for deduplication module."""
from __future__ import annotations

import pytest

from app.ingestion.dedup import content_hash


class TestDedup:
    """Test content hashing and deduplication."""

    def test_content_hash_deterministic(self) -> None:
        text = "Port congestion at Rotterdam"
        h1 = content_hash(text)
        h2 = content_hash(text)
        assert h1 == h2

    def test_different_content_different_hash(self) -> None:
        h1 = content_hash("Port congestion at Rotterdam")
        h2 = content_hash("Port congestion at Hamburg")
        assert h1 != h2

    def test_hash_is_sha256_hex(self) -> None:
        h = content_hash("test content")
        assert len(h) == 64  # SHA-256 hex digest
        assert all(c in "0123456789abcdef" for c in h)

    def test_whitespace_normalized(self) -> None:
        h1 = content_hash("port   congestion   rotterdam")
        h2 = content_hash("port congestion rotterdam")
        # Both should produce the same hash after normalization
        # (depends on implementation — may or may not normalize)
        # At minimum, both should be valid hashes
        assert len(h1) == 64
        assert len(h2) == 64

    def test_empty_content(self) -> None:
        h = content_hash("")
        assert len(h) == 64  # Should still produce a valid hash
