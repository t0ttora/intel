"""Intent classification (5 types: chokepoint, congestion, regulatory, freight, carrier)."""
from __future__ import annotations

import re
from dataclasses import dataclass

INTENT_PATTERNS: dict[str, list[str]] = {
    "chokepoint": [
        r"suez|panama|malacca|hormuz|bab.?el.?mandeb|strait|canal|chokepoint|blockage|grounding",
    ],
    "congestion": [
        r"congestion|delay|queue|dwell.?time|wait|backlog|bottleneck|port.?closure|overcrowded",
    ],
    "regulatory": [
        r"regulat|imo|emission|complian|customs|tariff|sanction|embargo|policy|mandate|rule",
    ],
    "freight": [
        r"freight|rate|scfi|wci|index|spot|contract|cost|price|surcharge|GRI|BAF",
    ],
    "carrier": [
        r"carrier|maersk|msc|cma.?cgm|hapag|cosco|evergreen|blank.?sail|service|alliance|capacity",
    ],
}


@dataclass
class IntentResult:
    """Classified intent with confidence scores."""

    primary_intent: str
    confidence: float
    all_scores: dict[str, float]


def classify_intent(query: str) -> IntentResult:
    """Classify a query into one of 5 intent types.

    Scores each intent based on keyword pattern matches.
    The highest-scoring intent becomes the primary intent.
    """
    query_lower = query.lower()
    scores: dict[str, float] = {}

    for intent, patterns in INTENT_PATTERNS.items():
        match_count = 0
        for pattern in patterns:
            matches = re.findall(pattern, query_lower, re.IGNORECASE)
            match_count += len(matches)

        # Normalize: each pattern match adds 0.2 confidence, capped at 0.95
        scores[intent] = min(0.95, match_count * 0.2)

    # If no intent matched, default to chokepoint with low confidence
    if all(s == 0 for s in scores.values()):
        scores["chokepoint"] = 0.3

    # Find primary intent
    primary = max(scores, key=lambda k: scores[k])
    confidence = scores[primary]

    # Set minimum confidence
    if confidence < 0.3:
        confidence = 0.3

    return IntentResult(
        primary_intent=primary,
        confidence=round(confidence, 2),
        all_scores={k: round(v, 2) for k, v in scores.items()},
    )
