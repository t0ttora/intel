"""Signal metadata tagger — transport mode & region classification.

Applied during ingestion to tag each signal with structured metadata
that enables hard pre-filtering at query time (FLAW 2 fix).
"""
from __future__ import annotations

import re

# ── Transport Mode Detection ────────────────────────────────────────────────
# Weighted keyword lists — longer/more specific patterns get higher weight.

_OCEAN_PATTERNS: list[tuple[str, int]] = [
    (r"\b(?:container\s*ship|bulk\s*carrier|tanker|vessel|vlcc|ulcv)\b", 3),
    (r"\b(?:ocean\s*freight|sea\s*freight|maritime\s*shipping)\b", 3),
    (r"\b(?:teu|feu|twenty.foot|forty.foot)\b", 2),
    (r"\b(?:port\s*congestion|berth|anchorage|draft\s*restriction)\b", 2),
    (r"\b(?:blank\s*sail|void\s*sail|slow\s*steam)\b", 2),
    (r"\b(?:ocean|maritime|shipping\s*line|carrier\s*alliance)\b", 1),
    (r"\b(?:maersk|msc|cma\s*cgm|cosco|evergreen|hapag|one|hmm|zim|yang\s*ming)\b", 2),
    (r"\b(?:suez|panama|strait|canal|cape\s*of\s*good\s*hope)\b", 2),
    (r"\b(?:port|dock|terminal|wharf|quay|stevedore|longshor)\b", 1),
    (r"\b(?:b/l|bill\s*of\s*lading|fcl|lcl|nvocc|demurrage|detention)\b", 1),
    (r"\b(?:scfi|wci|bdi|fbx|freight\s*index)\b", 2),
    (r"\b(?:roro|lng\s*carrier|lpg\s*carrier|ore\s*carrier)\b", 2),
    # v2.0 additions
    (r"\b(?:vessel\s*turnaround|port\s*dwell|chassis\s*pool|yard\s*congestion)\b", 2),
    (r"\b(?:reefer\s*plug|container\s*imbalance|equipment\s*repositioning)\b", 2),
    (r"\b(?:feeder\s*service|mother\s*vessel|transshipment|hub\s*port)\b", 2),
    (r"\b(?:bunker\s*surcharge|baf|caf|imo\s*2020|scrubber)\b", 1),
    (r"\b(?:dry\s*bulk|wet\s*bulk|break\s*bulk|neo.?panamax)\b", 2),
]

_AIR_PATTERNS: list[tuple[str, int]] = [
    (r"\b(?:air\s*freight|air\s*cargo|belly\s*cargo|freighter\s*aircraft)\b", 3),
    (r"\b(?:airline|aircraft|airport|runway|tarmac)\b", 2),
    (r"\b(?:iata|awb|air\s*waybill|hawb|mawb)\b", 2),
    (r"\b(?:uld|unit\s*load\s*device|pallet\s*position)\b", 2),
    (r"\b(?:bafi|air\s*freight\s*index|tact\s*rate)\b", 2),
    (r"\b(?:charter\s*flight|cargo\s*plane|wide.?body)\b", 2),
    (r"\b(?:gsa|general\s*sales\s*agent)\b", 1),
    # v2.0 additions
    (r"\b(?:freighter\s*conversion|passenger.to.freighter|p2f|belly.hold)\b", 3),
    (r"\b(?:load\s*factor|cargo\s*load\s*factor|clr|chargeable\s*weight)\b", 2),
    (r"\b(?:e.?commerce\s*air|express\s*freight|integrator)\b", 2),
    (r"\b(?:pharma\s*cold\s*chain|temp.?controlled|perishable\s*cargo)\b", 2),
    (r"\b(?:ground\s*handling|gha|ramp\s*handling|cargo\s*terminal)\b", 2),
    (r"\b(?:slot\s*restriction|curfew|noise\s*abatement|overflight)\b", 1),
    (r"\b(?:tac\s*index|clive\s*data|xeneta\s*air|worldacd)\b", 2),
    (r"\b(?:atlas\s*air|cargolux|fedex|ups\s*air|dhl\s*express|qatar\s*cargo|emirates\s*skycargo)\b", 2),
]

_RAIL_PATTERNS: list[tuple[str, int]] = [
    (r"\b(?:rail\s*freight|railway|railroad|intermodal\s*rail)\b", 3),
    (r"\b(?:block\s*train|unit\s*train|trainload)\b", 2),
    (r"\b(?:china.europe\s*rail|land\s*bridge|trans.siberian)\b", 3),
    (r"\b(?:silk\s*road|new\s*silk\s*road|belt\s*and\s*road|bri)\b", 3),
    (r"\b(?:cr\s*express|china\s*railway\s*express|cre|yuxinou|chengdu.europe|yiwu.europe)\b", 3),
    (r"\b(?:khorgos|dostyk|mala(?:szewicze)?|brest|alashankou|erenhot|naushki)\b", 2),
    (r"\b(?:eurasian?\s*rail|eurasian?\s*corridor|middle\s*corridor|trans.?caspian)\b", 3),
    (r"\b(?:rail\s*car|wagon|locomotive|marshalling\s*yard)\b", 2),
    (r"\b(?:intermodal\s*terminal|rail\s*terminal|rail\s*hub)\b", 2),
    # v2.0 additions
    (r"\b(?:intermodal\s*ramp|ramp\s*congestion|ramp\s*capacity)\b", 2),
    (r"\b(?:dwell\s*time|terminal\s*dwell|rail\s*dwell)\b", 2),
    (r"\b(?:railcar\s*shortage|car\s*supply|car\s*order)\b", 2),
    (r"\b(?:psr|precision\s*scheduled\s*railroading)\b", 3),
    (r"\b(?:terminal\s*velocity|gate\s*cycle|gate\s*turn)\b", 2),
    (r"\b(?:double.?stack|stack\s*train|well\s*car|spine\s*car)\b", 2),
    (r"\b(?:class\s*[i1]\s*railroad|shortline|switching\s*yard)\b", 2),
    (r"\b(?:union\s*pacific|bnsf|csx|norfolk\s*southern|cn\s*rail|cp\s*rail|kansas\s*city\s*southern)\b", 2),
]

_ROAD_PATTERNS: list[tuple[str, int]] = [
    (r"\b(?:truck(?:ing)?|drayage|road\s*freight|road\s*transport)\b", 3),
    (r"\b(?:chassis|trailer|flatbed|reefer\s*truck)\b", 2),
    (r"\b(?:last\s*mile|first\s*mile|cross.dock)\b", 2),
    (r"\b(?:highway|toll|border\s*crossing|customs\s*checkpoint)\b", 1),
    (r"\b(?:fleet|driver\s*shortage|hours\s*of\s*service)\b", 1),
    # v2.0 additions
    (r"\b(?:spot\s*rate|contract\s*rate|lane\s*rate|truckload\s*rate)\b", 2),
    (r"\b(?:deadhead|dead\s*head|empty\s*miles|repositioning)\b", 2),
    (r"\b(?:detention\s*time|lumper\s*fee|accessorial)\b", 2),
    (r"\b(?:eld\s*mandate|electronic\s*logging|hos\s*violation)\b", 2),
    (r"\b(?:broker\s*margin|carrier\s*rate|load\s*board)\b", 2),
    (r"\b(?:ltl|less.than.truckload|ftl|full\s*truckload|partial\s*load)\b", 2),
    (r"\b(?:dat\s*load\s*board|truckstop\.com|loadboard)\b", 2),
    (r"\b(?:owner.?operator|o/o|lease.?purchase|fleet\s*size)\b", 1),
    (r"\b(?:fuel\s*surcharge|diesel\s*price|fuel\s*cost)\b", 1),
]

# ── Macro / Supply Chain Patterns (NEW — v2.0) ─────────────────────────────
_MACRO_PATTERNS: list[tuple[str, int]] = [
    (r"\b(?:inventory\s*glut|inventory\s*surplus|overstock|excess\s*inventory)\b", 2),
    (r"\b(?:demand\s*soften|demand\s*weak|consumption\s*decline|order\s*cancel)\b", 2),
    (r"\b(?:reshoring|nearshoring|friend.?shoring|onshoring)\b", 3),
    (r"\b(?:trade\s*war|tariff\s*escalat|tariff\s*hike|retaliatory\s*tariff)\b", 3),
    (r"\b(?:sanction|embargo|export\s*control|entity\s*list)\b", 2),
    (r"\b(?:supply\s*chain\s*resilience|dual\s*sourcing|supply\s*chain\s*diversif)\b", 2),
    (r"\b(?:pmi|purchasing\s*managers?\s*index|manufacturing\s*index)\b", 2),
    (r"\b(?:gdp|economic\s*growth|recession|stagflation)\b", 1),
    (r"\b(?:consumer\s*spending|retail\s*sales|import\s*volume)\b", 1),
]

# ── Cyber / Risk Patterns (NEW — v2.0) ─────────────────────────────────────
_CYBER_PATTERNS: list[tuple[str, int]] = [
    (r"\b(?:ransomware|malware|cyberattack|cyber.?attack)\b", 3),
    (r"\b(?:scada|ics|industrial\s*control|operational\s*technology|ot\s*security)\b", 3),
    (r"\b(?:data\s*breach|exfiltration|phishing|spear.?phishing)\b", 2),
    (r"\b(?:port\s*system|terminal\s*system|shipping\s*system)\b", 1),
    (r"\b(?:gps\s*spoofing|ais\s*spoofing|navigation\s*attack)\b", 3),
    (r"\b(?:supply\s*chain\s*attack|software\s*supply\s*chain)\b", 2),
]


def detect_transport_mode(text: str) -> str | None:
    """Classify transport mode from signal content.

    Returns 'ocean', 'air', 'rail', 'road', or None if no clear signal.
    Requires a minimum score of 2 to classify (prevents false positives).
    """
    text_lower = text.lower()
    scores: dict[str, int] = {"ocean": 0, "air": 0, "rail": 0, "road": 0}

    for pattern, weight in _OCEAN_PATTERNS:
        if re.search(pattern, text_lower):
            scores["ocean"] += weight

    for pattern, weight in _AIR_PATTERNS:
        if re.search(pattern, text_lower):
            scores["air"] += weight

    for pattern, weight in _RAIL_PATTERNS:
        if re.search(pattern, text_lower):
            scores["rail"] += weight

    for pattern, weight in _ROAD_PATTERNS:
        if re.search(pattern, text_lower):
            scores["road"] += weight

    # Must have minimum score of 2 to classify
    max_mode = max(scores, key=scores.get)  # type: ignore[arg-type]
    if scores[max_mode] < 2:
        return None

    # Require a clear winner (at least 2x the runner-up) to avoid ambiguity
    sorted_scores = sorted(scores.values(), reverse=True)
    if sorted_scores[1] > 0 and sorted_scores[0] < sorted_scores[1] * 2:
        return "multimodal"  # Multiple modes detected — tag as multimodal

    return max_mode


def detect_macro_signal(text: str) -> bool:
    """Return True if text contains macro/supply-chain-level signals."""
    text_lower = text.lower()
    score = 0
    for pattern, weight in _MACRO_PATTERNS:
        if re.search(pattern, text_lower):
            score += weight
    return score >= 2


def detect_cyber_signal(text: str) -> bool:
    """Return True if text contains cyber/risk intelligence signals."""
    text_lower = text.lower()
    score = 0
    for pattern, weight in _CYBER_PATTERNS:
        if re.search(pattern, text_lower):
            score += weight
    return score >= 2
    """Classify transport mode from signal content.

    Returns 'ocean', 'air', 'rail', 'road', or None if no clear signal.
    Requires a minimum score of 2 to classify (prevents false positives).
    """
    text_lower = text.lower()
    scores: dict[str, int] = {"ocean": 0, "air": 0, "rail": 0, "road": 0}

    for pattern, weight in _OCEAN_PATTERNS:
        if re.search(pattern, text_lower):
            scores["ocean"] += weight

    for pattern, weight in _AIR_PATTERNS:
        if re.search(pattern, text_lower):
            scores["air"] += weight

    for pattern, weight in _RAIL_PATTERNS:
        if re.search(pattern, text_lower):
            scores["rail"] += weight

    for pattern, weight in _ROAD_PATTERNS:
        if re.search(pattern, text_lower):
            scores["road"] += weight

    # Must have minimum score of 2 to classify
    max_mode = max(scores, key=scores.get)  # type: ignore[arg-type]
    if scores[max_mode] < 2:
        return None

    # Require a clear winner (at least 2x the runner-up) to avoid ambiguity
    sorted_scores = sorted(scores.values(), reverse=True)
    if sorted_scores[1] > 0 and sorted_scores[0] < sorted_scores[1] * 2:
        return "multimodal"  # Multiple modes detected — tag as multimodal

    return max_mode


# ── Region Detection ────────────────────────────────────────────────────────
# Maps geographic indicators to canonical region codes.

_REGION_PATTERNS: list[tuple[str, str]] = [
    # North America
    (r"\b(?:us\s*east\s*coast|usec|new\s*york|savannah|charleston|norfolk|port\s*newark|miami|jacksonville)\b", "USEC"),
    (r"\b(?:us\s*west\s*coast|uswc|los\s*angeles|long\s*beach|oakland|seattle|tacoma)\b", "USWC"),
    (r"\b(?:us\s*gulf|houston|new\s*orleans|mobile|gulf\s*coast)\b", "US_GULF"),
    (r"\b(?:canada|vancouver|montreal|prince\s*rupert|halifax)\b", "CANADA"),
    # Asia
    (r"\b(?:china|shanghai|shenzhen|ningbo|qingdao|tianjin|xiamen|guangzhou|yantian)\b", "CHINA"),
    (r"\b(?:south\s*(?:east\s*)?asia|vietnam|thailand|indonesia|malaysia|philippines|singapore|ho\s*chi\s*minh|laem\s*chabang|tanjung\s*pelepas|port\s*klang)\b", "SE_ASIA"),
    (r"\b(?:japan|tokyo|yokohama|kobe|nagoya)\b", "JAPAN"),
    (r"\b(?:south\s*korea|korea|busan|incheon)\b", "KOREA"),
    (r"\b(?:india|mumbai|nhava\s*sheva|chennai|mundra|jnpt|kolkata)\b", "INDIA"),
    (r"\b(?:taiwan|kaohsiung|keelung|taichung)\b", "TAIWAN"),
    # Central Asia / Eurasian Corridor
    (r"\b(?:central\s*asia|kazakhstan|uzbekistan|turkmenistan|kyrgyzstan|tajikistan)\b", "CENTRAL_ASIA"),
    (r"\b(?:khorgos|dostyk|alashankou|erenhot|mala(?:szewicze)?|brest|naushki)\b", "CENTRAL_ASIA"),
    (r"\b(?:russia|moscow|vladimir(?:ostok)?|novosibirsk|trans.?siberian)\b", "RUSSIA"),
    # Europe
    (r"\b(?:north\s*europe|rotterdam|hamburg|antwerp|bremerhaven|felixstowe|le\s*havre)\b", "N_EUROPE"),
    (r"\b(?:mediterranean|med\s*ports?|piraeus|valencia|barcelona|genoa|algeciras|gioia\s*tauro|marseille|fos)\b", "MED"),
    (r"\b(?:baltic|gdansk|gothenburg|st\s*petersburg|tallinn|riga)\b", "BALTIC"),
    (r"\b(?:uk|united\s*kingdom|britain|london\s*gateway|southampton|liverpool|tilbury)\b", "UK"),
    # Middle East & Africa
    (r"\b(?:middle\s*east|persian\s*gulf|uae|dubai|jebel\s*ali|khalifa|abu\s*dhabi|oman|salalah|saudi|jeddah|dammam)\b", "MIDDLE_EAST"),
    (r"\b(?:red\s*sea|suez|aden|houthi|bab.el.mandeb)\b", "RED_SEA"),
    (r"\b(?:east\s*africa|mombasa|dar\s*es\s*salaam|djibouti)\b", "E_AFRICA"),
    (r"\b(?:west\s*africa|lagos|tema|lome|abidjan)\b", "W_AFRICA"),
    (r"\b(?:south\s*africa|durban|cape\s*town|port\s*elizabeth)\b", "S_AFRICA"),
    # Oceania
    (r"\b(?:australia|sydney|melbourne|brisbane|fremantle)\b", "AUSTRALIA"),
    (r"\b(?:new\s*zealand|auckland|tauranga)\b", "NEW_ZEALAND"),
    # Latin America
    (r"\b(?:brazil|santos|paranagua|itajai|navegantes)\b", "BRAZIL"),
    (r"\b(?:panama|colon|balboa|panama\s*canal)\b", "PANAMA"),
    (r"\b(?:mexico|manzanillo|lazaro\s*cardenas|veracruz|altamira)\b", "MEXICO"),
    (r"\b(?:chile|san\s*antonio|valparaiso)\b", "CHILE"),
    (r"\b(?:colombia|cartagena|buenaventura)\b", "COLOMBIA"),
    (r"\b(?:argentina|buenos\s*aires)\b", "ARGENTINA"),
]


def detect_region(text: str) -> str | None:
    """Detect the primary geographic region from signal content.

    Returns a canonical region code or None.
    If multiple regions are detected, returns the one with the most matches.
    """
    text_lower = text.lower()
    region_hits: dict[str, int] = {}

    for pattern, region in _REGION_PATTERNS:
        matches = re.findall(pattern, text_lower)
        if matches:
            region_hits[region] = region_hits.get(region, 0) + len(matches)

    if not region_hits:
        return None

    # Return the region with the most keyword hits
    return max(region_hits, key=region_hits.get)  # type: ignore[arg-type]


def tag_signal(text: str) -> tuple[str | None, str | None]:
    """Convenience: detect both transport_mode and region from text.

    Returns (transport_mode, region).
    """
    return detect_transport_mode(text), detect_region(text)


def tag_signal_extended(text: str) -> dict:
    """Extended tagging — returns mode, region, and flags for macro/cyber.

    Returns dict with keys: transport_mode, region, is_macro, is_cyber.
    """
    return {
        "transport_mode": detect_transport_mode(text),
        "region": detect_region(text),
        "is_macro": detect_macro_signal(text),
        "is_cyber": detect_cyber_signal(text),
    }
