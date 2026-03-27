"""Tests for calibration system."""
from __future__ import annotations

import pytest

from app.calibration.source_weights import calibrate_source_weight
from app.calibration.formula_weights import _pearson_correlation


class TestCalibration:
    """Test weight calibration functions."""

    def test_calibrate_source_weight_correct(self) -> None:
        """When prediction was correct, weight should increase."""
        new_weight = calibrate_source_weight(
            current_weight=0.50,
            was_correct=True,
            learning_rate=0.05,
        )
        assert new_weight > 0.50

    def test_calibrate_source_weight_incorrect(self) -> None:
        """When prediction was incorrect, weight should decrease."""
        new_weight = calibrate_source_weight(
            current_weight=0.50,
            was_correct=False,
            learning_rate=0.05,
        )
        assert new_weight < 0.50

    def test_calibrate_weight_floor(self) -> None:
        """Weight should not go below floor (0.10)."""
        new_weight = calibrate_source_weight(
            current_weight=0.12,
            was_correct=False,
            learning_rate=0.05,
        )
        assert new_weight >= 0.10

    def test_calibrate_weight_ceiling(self) -> None:
        """Weight should not exceed ceiling (0.95)."""
        new_weight = calibrate_source_weight(
            current_weight=0.93,
            was_correct=True,
            learning_rate=0.05,
        )
        assert new_weight <= 0.95

    def test_pearson_perfect_positive(self) -> None:
        """Perfect positive correlation should be ~1.0."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        r = _pearson_correlation(x, y)
        assert abs(r - 1.0) < 0.01

    def test_pearson_perfect_negative(self) -> None:
        """Perfect negative correlation should be ~-1.0."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [10.0, 8.0, 6.0, 4.0, 2.0]
        r = _pearson_correlation(x, y)
        assert abs(r - (-1.0)) < 0.01

    def test_pearson_no_correlation(self) -> None:
        """Uncorrelated data should give r near 0."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [5.0, 1.0, 4.0, 2.0, 3.0]
        r = _pearson_correlation(x, y)
        assert abs(r) < 0.5

    def test_pearson_insufficient_data(self) -> None:
        """With too few points, should return 0."""
        r = _pearson_correlation([1.0], [2.0])
        assert r == 0.0
