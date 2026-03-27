"""Noise Control — filter low-quality signals before event clustering.

Filters:
1. Risk score below relevance threshold (< 0.20)
2. Duplicate headlines (Levenshtein ratio > 0.85)
3. Single human-only source with low confidence (< 0.40)
"""
from __future__ import annotations

import logging

from app.db.models import Signal

logger = logging.getLogger(__name__)

RISK_FLOOR = 0.20
TITLE_SIMILARITY_THRESHOLD = 0.85
LOW_CONFIDENCE_THRESHOLD = 0.40

# Sources considered "human-only" (social, forums — no editorial process)
HUMAN_ONLY_SOURCES: set[str] = {
    "reddit_shipping",
    "reddit_logistics",
    "reddit_supplychain",
    "reddit_trade",
    "twitter_maritime",
    "gcaptain_forum",
}


def _levenshtein_ratio(s1: str, s2: str) -> float:
    """Compute normalized Levenshtein similarity ratio (0-1). 1.0 = identical."""
    if s1 == s2:
        return 1.0
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0

    # Optimized two-row DP
    prev = list(range(len2 + 1))
    curr = [0] * (len2 + 1)

    for i in range(1, len1 + 1):
        curr[0] = i
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            curr[j] = min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost)
        prev, curr = curr, prev

    distance = prev[len2]
    max_len = max(len1, len2)
    return 1.0 - (distance / max_len)


def filter_noise(signals: list[Signal]) -> list[Signal]:
    """Filter out noise signals before clustering.

    Returns a cleaned list of signals that pass all quality gates.
    """
    if not signals:
        return []

    original_count = len(signals)
    passed: list[Signal] = []
    seen_titles: list[str] = []

    dropped_risk = 0
    dropped_dup = 0
    dropped_human = 0

    for sig in signals:
        # Gate 1: Risk floor
        if (sig.risk_score or 0) < RISK_FLOOR:
            dropped_risk += 1
            continue

        # Gate 2: Duplicate title detection
        title = (sig.title or "").strip().lower()
        if title:
            is_dup = False
            for existing_title in seen_titles:
                if _levenshtein_ratio(title, existing_title) > TITLE_SIMILARITY_THRESHOLD:
                    is_dup = True
                    break
            if is_dup:
                dropped_dup += 1
                continue
            seen_titles.append(title)

        # Gate 3: Low-confidence human-only source
        if sig.source in HUMAN_ONLY_SOURCES:
            source_weight = sig.source_weight or 0.5
            if source_weight < LOW_CONFIDENCE_THRESHOLD:
                dropped_human += 1
                continue

        passed.append(sig)

    logger.info(
        f"Noise control: {original_count} → {len(passed)} signals "
        f"(dropped: {dropped_risk} risk, {dropped_dup} dup, {dropped_human} human-only)"
    )
    return passed
