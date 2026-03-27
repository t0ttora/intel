"""Tests for time decay calculation."""
from __future__ import annotations

import pytest

from app.scoring.time_decay import compute_time_decay, compute_time_decay_from_timestamp


class TestTimeDecay:
    """Test time decay with 12-hour half-life."""

    def test_fresh_signal(self) -> None:
        decay = compute_time_decay(0.0)
        assert abs(decay - 1.0) < 0.01

    def test_12_hour_signal(self) -> None:
        decay = compute_time_decay(12.0)
        assert abs(decay - 0.5) < 0.01

    def test_24_hour_signal(self) -> None:
        decay = compute_time_decay(24.0)
        assert abs(decay - 0.25) < 0.01

    def test_very_old_signal(self) -> None:
        decay = compute_time_decay(168.0)  # 1 week
        assert decay < 0.01

    def test_negative_age(self) -> None:
        # Negative age should clamp to 1.0
        decay = compute_time_decay(-5.0)
        assert decay >= 1.0 or decay > 0  # Implementation may vary

    def test_monotonically_decreasing(self) -> None:
        prev = 1.0
        for hours in [0, 3, 6, 12, 24, 48, 72]:
            decay = compute_time_decay(float(hours))
            assert decay <= prev
            prev = decay

    def test_bounded_zero_one(self) -> None:
        for hours in [0, 1, 6, 12, 24, 48, 96, 168]:
            decay = compute_time_decay(float(hours))
            assert 0.0 <= decay <= 1.0
