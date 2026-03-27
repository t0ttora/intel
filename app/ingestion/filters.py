"""Keyword gate (regex) — logistics terms, chokepoints, carriers."""
from __future__ import annotations

import re

LOGISTICS_KEYWORDS = re.compile(
    r"(?i)\b("
    r"port|freight|container|vessel|shipping|logistics|cargo|TEU|FEU|"
    r"maritime|tanker|bulk|carrier|maersk|msc|cma.?cgm|hapag|cosco|evergreen|"
    r"suez|panama|malacca|hormuz|bab.?el.?mandeb|rotterdam|hamburg|shanghai|singapore|"
    r"AIS|dwell.?time|blank.?sailing|reroute|congestion|delay|strike|blockade|"
    r"SCFI|WCI|freightos|drewry|"
    r"IMO|UKMTO|customs|tariff|embargo|sanctions"
    r")\b"
)


def passes_keyword_filter(text: str) -> bool:
    """Return True if the text matches at least one logistics keyword."""
    return bool(LOGISTICS_KEYWORDS.search(text))


def count_keyword_matches(text: str) -> int:
    """Count the number of unique keyword matches in the text."""
    matches = LOGISTICS_KEYWORDS.findall(text)
    return len(set(m.lower() for m in matches))
