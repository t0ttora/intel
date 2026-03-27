"""Exponential time decay: 1.0 at T+0, 0.5 at T+12h, 0.1 at T+72h."""
from __future__ import annotations

import math
from datetime import datetime, timezone

HALF_LIFE_HOURS = 12.0


def compute_time_decay(signal_age_hours: float) -> float:
    """Exponential decay: 1.0 at T+0, 0.5 at T+12h, 0.1 at T+72h."""
    if signal_age_hours <= 0:
        return 1.0
    return round(math.exp(-0.693 * signal_age_hours / HALF_LIFE_HOURS), 4)


def compute_time_decay_from_timestamp(created_at: datetime) -> float:
    """Compute time decay from a signal's creation timestamp."""
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_hours = (now - created_at).total_seconds() / 3600.0
    return compute_time_decay(age_hours)
