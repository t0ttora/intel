"""Intent classification (6 types: chokepoint, congestion, regulatory, freight, carrier, labor)."""
from __future__ import annotations

import re
from dataclasses import dataclass

INTENT_PATTERNS: dict[str, list[str]] = {
    "chokepoint": [
        r"suez|panama|malacca|hormuz|bab.?el.?mandeb|strait|canal|chokepoint|blockage|grounding",
        r"cape.?of.?good.?hope|red.?sea|route.?deviation|reroute|diversion",
        r"houthi|piracy|war.?risk|maritime.?security|attack|threat",
    ],
    "congestion": [
        r"congestion|delay|queue|dwell.?time|wait|backlog|bottleneck|port.?closure|overcrowded",
        r"berth|anchorage|vessel.?queue|terminal|yard.?capacity|chassis.?shortage",
        r"blank.?sail|void.?sail|capacity.?reduction|omit|skip.*port",
    ],
    "regulatory": [
        r"regulat|imo|mepc|emission|complian|customs|tariff|sanction|embargo|policy|mandate|rule",
        r"eu.?ets|cbam|carbon|imo.?2020|imo.?2023|sulphur|ballast|inspection",
        r"usmca|rcep|trade.?war|duties|anti.?dumping|countervailing",
    ],
    "freight": [
        r"freight|rate|scfi|wci|bdi|bafi|fbx|index|spot|contract|cost|price|surcharge",
        r"gri|baf|thc|psf|peak.?season|bunker|fuel|rate.?increase|rate.?hike",
        r"teu|feu|container.?rate|booking|capacity.?crunch|demand|supply",
    ],
    "carrier": [
        r"carrier|maersk|msc|cma.?cgm|hapag|cosco|evergreen|zim|hmm|one|oocl|pil",
        r"blank.?sail|service|alliance|2m|the.?alliance|ocean.?alliance|gemini",
        r"schedule|rotation|vessel.?deploy|fleet|newbuild|charter",
    ],
    "labor": [
        r"strike|union|ila|ilwu|pma|itf|dock.?work|longshore|stevedore|picket",
        r"labor|labour|work.?stoppage|walkout|lockout|negotiat|collective.?bargain",
        r"port.?shut|terminal.?clos|industrial.?action|stand.?down",
    ],
}


@dataclass
class IntentResult:
    """Classified intent with confidence scores."""

    primary_intent: str
    confidence: float
    all_scores: dict[str, float]


def classify_intent(query: str) -> IntentResult:
    """Classify a query into one of 6 intent types.

    Scores each intent based on keyword pattern matches.
    The highest-scoring intent becomes the primary intent.
    Uses the expanded query (with ontology injection) for broader coverage.
    """
    from app.intelligence.query_expander import expand_query

    # Expand the query with ontology context before classification
    expanded = expand_query(query)
    query_lower = expanded.lower()
    scores: dict[str, float] = {}

    for intent, patterns in INTENT_PATTERNS.items():
        match_count = 0
        for pattern in patterns:
            matches = re.findall(pattern, query_lower, re.IGNORECASE)
            match_count += len(matches)

        # Normalize: each pattern match adds 0.15 confidence, capped at 0.95
        scores[intent] = min(0.95, match_count * 0.15)

    # If no intent matched, classify as unknown
    if all(s == 0 for s in scores.values()):
        scores["unknown"] = 0.10
        return IntentResult(
            primary_intent="unknown",
            confidence=0.10,
            all_scores={k: round(v, 2) for k, v in scores.items()},
        )

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
