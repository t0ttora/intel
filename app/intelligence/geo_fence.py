"""Geographic fencing — strict per-signal region filtering.

Applied after RAG retrieval, BEFORE context is sent to the LLM.
Each signal is individually checked against the query's target region.
Incompatible signals are silently dropped — no mercy, no benefit of the doubt.
"""
from __future__ import annotations

import logging
from typing import Any

from app.intelligence.signal_tagger import detect_region

logger = logging.getLogger(__name__)

# US / North-America region family — treated as a single block for rejection.
_US_NA_FAMILY: set[str] = {"USEC", "USWC", "US_GULF", "CANADA", "MEXICO"}


def _resolve_signal_region(sig: Any) -> str | None:
    """Extract a signal's region — try tag first, then content analysis."""
    region = getattr(sig, "region", None)
    if region:
        return region
    # Fall back to full-text region detection
    content = getattr(sig, "content", "") or ""
    title = getattr(sig, "title", "") or ""
    geo_zone = getattr(sig, "geo_zone", "") or ""
    return detect_region(f"{title} {content} {geo_zone}")


def apply_geo_fence(
    signals: list,
    query: str,
    query_region: str | None,
) -> list:
    """Filter signals per-signal, dropping any whose region is incompatible.

    Strict mode:
    - Each signal's region tag is checked individually.
    - If a signal has no detectable region AND the query has a clear
      regional target, the signal is dropped (no benefit of the doubt).
    - Signals from completely unrelated region families (e.g. US/NA
      signals when the query targets Eurasian corridor) are hard-rejected.

    Returns:
        Filtered list. Empty list triggers INSUFFICIENT — Geographic mismatch.
    """
    # Resolve query region from text if not pre-detected
    if not query_region:
        query_region = detect_region(query)

    if not query_region:
        # No geographic constraint in query — pass all signals through
        return signals

    from app.intelligence.query_pipeline import _COMPATIBLE_REGIONS

    compatible = _COMPATIBLE_REGIONS.get(query_region, set())
    allowed_regions = {query_region} | compatible

    kept: list = []
    rejected_mismatch = 0
    rejected_untagged = 0

    for sig in signals:
        sig_region = _resolve_signal_region(sig)

        if not sig_region:
            # Strict mode: untagged signal with a region-specific query → drop.
            # We cannot guarantee it belongs to the target area.
            rejected_untagged += 1
            logger.debug(
                f"Geo-fence DROP (no region tag): "
                f"{getattr(sig, 'title', '?')[:60]}"
            )
            continue

        if sig_region in allowed_regions:
            kept.append(sig)
        else:
            rejected_mismatch += 1
            logger.debug(
                f"Geo-fence DROP (region mismatch: query={query_region}, "
                f"signal={sig_region}): {getattr(sig, 'title', '?')[:60]}"
            )

    total_rejected = rejected_mismatch + rejected_untagged
    if total_rejected > 0:
        logger.info(
            f"Geo-fence: kept {len(kept)}/{len(signals)} signals "
            f"(rejected {rejected_mismatch} mismatch + {rejected_untagged} untagged "
            f"for query_region={query_region})"
        )

    return kept
