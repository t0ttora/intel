"""Tests for ingestion filters."""
from __future__ import annotations

import pytest

from app.ingestion.filters import passes_keyword_filter, count_keyword_matches


class TestKeywordFilter:
    """Test the logistics keyword filter."""

    def test_passes_logistics_content(self) -> None:
        text = "Major port congestion reported at Rotterdam due to severe weather"
        assert passes_keyword_filter(text) is True

    def test_passes_shipping_content(self) -> None:
        text = "Container vessel Ever Given blocks Suez Canal shipping lane"
        assert passes_keyword_filter(text) is True

    def test_passes_freight_content(self) -> None:
        text = "Freight rates surge on Asia-Europe route amid supply chain disruption"
        assert passes_keyword_filter(text) is True

    def test_rejects_unrelated_content(self) -> None:
        text = "The latest smartphone review shows improved battery life and camera quality"
        assert passes_keyword_filter(text) is False

    def test_rejects_empty_content(self) -> None:
        assert passes_keyword_filter("") is False

    def test_rejects_short_content(self) -> None:
        assert passes_keyword_filter("hello world") is False

    def test_case_insensitive(self) -> None:
        text = "MAJOR PORT CONGESTION at ROTTERDAM"
        assert passes_keyword_filter(text) is True

    def test_count_matches(self) -> None:
        text = "Port congestion at Rotterdam causes shipping delays and freight backlogs"
        count = count_keyword_matches(text)
        assert count >= 3  # port, congestion, shipping, freight, delay

    def test_count_no_matches(self) -> None:
        text = "The weather is nice today"
        count = count_keyword_matches(text)
        assert count == 0
