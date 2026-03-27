"""Geo-criticality index lookup."""
from __future__ import annotations

GEO_CRITICALITY: dict[str, float] = {
    "suez_canal": 1.00,
    "strait_of_malacca": 0.95,
    "panama_canal": 0.90,
    "bab_el_mandeb": 0.90,
    "hormuz": 0.90,
    "shanghai": 0.85,
    "ningbo": 0.85,
    "singapore": 0.85,
    "rotterdam": 0.80,
    "hamburg": 0.80,
    "los_angeles": 0.75,
    "long_beach": 0.75,
    "busan": 0.60,
    "colombo": 0.60,
    "piraeus": 0.60,
    "valencia": 0.55,
    "jeddah": 0.50,
}

# Default for unknown zones (regional feeder level)
DEFAULT_GEO_CRITICALITY = 0.30


def get_geo_criticality(zone: str) -> float:
    """Return the geo-criticality score for a zone. Default: 0.30."""
    return GEO_CRITICALITY.get(zone, DEFAULT_GEO_CRITICALITY)


def detect_geo_zone(text: str) -> str | None:
    """Attempt to detect a geo zone from text content."""
    text_lower = text.lower()

    # Ordered by specificity — more specific patterns first
    zone_patterns: list[tuple[str, list[str]]] = [
        ("bab_el_mandeb", ["bab el mandeb", "bab-el-mandeb", "bab al-mandab"]),
        ("strait_of_malacca", ["malacca", "strait of malacca"]),
        ("suez_canal", ["suez canal", "suez"]),
        ("panama_canal", ["panama canal", "panama"]),
        ("hormuz", ["strait of hormuz", "hormuz"]),
        ("shanghai", ["shanghai", "yangshan"]),
        ("ningbo", ["ningbo", "zhoushan"]),
        ("singapore", ["singapore", "tanjung pelepas"]),
        ("rotterdam", ["rotterdam", "europoort"]),
        ("hamburg", ["hamburg"]),
        ("los_angeles", ["los angeles", "port of la"]),
        ("long_beach", ["long beach"]),
        ("busan", ["busan"]),
        ("colombo", ["colombo"]),
        ("piraeus", ["piraeus"]),
        ("valencia", ["valencia"]),
        ("jeddah", ["jeddah", "jeddah islamic port"]),
    ]

    for zone, patterns in zone_patterns:
        for pattern in patterns:
            if pattern in text_lower:
                return zone

    return None
