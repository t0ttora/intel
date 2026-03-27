"""Query expansion — domain ontology injection + acronym resolution.

Pre-processes user queries before intent classification to handle
industry-specific jargon, acronyms, and entity names that the
lexical intent classifier would otherwise miss.
"""
from __future__ import annotations

import re

# ── Logistics Acronym Ontology ──────────────────────────────────────────────
# Maps acronyms/abbreviations to their expanded forms plus context keywords
# that help both the intent classifier and the embedding model.

ACRONYM_ONTOLOGY: dict[str, str] = {
    # Unions & labor
    "ila": "International Longshoremen's Association port union dock workers strike",
    "ilwu": "International Longshore and Warehouse Union west coast port strike",
    "pma": "Pacific Maritime Association port employer labor negotiations",
    "itu": "International Transport Workers' Federation seafarer union",
    "itf": "International Transport Workers' Federation maritime labor",
    "nmeu": "National Maritime Employees Union dock workers",
    # Regulatory bodies
    "imo": "International Maritime Organization regulations shipping safety",
    "ukmto": "United Kingdom Maritime Trade Operations naval security advisory",
    "msc": "Maritime Safety Committee safety regulations",
    "mepc": "Marine Environment Protection Committee emissions pollution",
    "iacs": "International Association of Classification Societies hull inspection",
    "emsa": "European Maritime Safety Agency eu regulations",
    "amsa": "Australian Maritime Safety Authority maritime safety",
    "mpa": "Maritime and Port Authority of Singapore port regulations",
    # Trade zones & blocs
    "usmca": "United States-Mexico-Canada Agreement trade tariff",
    "rcep": "Regional Comprehensive Economic Partnership asia trade",
    "eu ets": "European Union Emissions Trading System carbon shipping",
    "cbam": "Carbon Border Adjustment Mechanism eu tariff carbon",
    "usec": "United States East Coast ports",
    "uswc": "United States West Coast ports",
    "naccs": "Nippon Automated Cargo and Port Consolidated System japan customs",
    # Freight indices
    "scfi": "Shanghai Containerized Freight Index container rates spot market",
    "wci": "World Container Index Drewry freight rate benchmark",
    "bdi": "Baltic Dry Index bulk carrier freight rate",
    "bafi": "Baltic Air Freight Index air cargo rates",
    "fbx": "Freightos Baltic Index container shipping rates",
    "gri": "General Rate Increase freight surcharge carrier",
    "baf": "Bunker Adjustment Factor fuel surcharge",
    "thc": "Terminal Handling Charge port fee container",
    "psf": "Peak Season Surcharge freight carrier congestion",
    "eas": "Emergency Anchorage Surcharge fuel deviation",
    # Container/vessel types
    "teu": "twenty-foot equivalent unit container freight capacity",
    "feu": "forty-foot equivalent unit container shipping",
    "ulcv": "Ultra Large Container Vessel mega-ship capacity",
    "vlcc": "Very Large Crude Carrier tanker oil shipping",
    "ulcc": "Ultra Large Crude Carrier supertanker oil",
    "lng": "Liquefied Natural Gas tanker energy shipping",
    "lpg": "Liquefied Petroleum Gas carrier energy shipping",
    "roro": "Roll-on Roll-off vehicle carrier auto shipping",
    "vloc": "Very Large Ore Carrier bulk mining shipping",
    # Shipping terms
    "ais": "Automatic Identification System vessel tracking maritime",
    "eta": "Estimated Time of Arrival port vessel shipping",
    "etd": "Estimated Time of Departure port vessel shipping",
    "ets": "Estimated Time of Sailing vessel departure port",
    "b/l": "Bill of Lading shipping document cargo",
    "fcl": "Full Container Load shipping freight",
    "lcl": "Less than Container Load consolidation freight",
    "fob": "Free on Board trade terms shipping",
    "cif": "Cost Insurance Freight trade terms shipping",
    "ddp": "Delivered Duty Paid trade terms shipping",
    # Air freight
    "iata": "International Air Transport Association airline cargo",
    "tact": "The Air Cargo Tariff iata rates pricing",
    "awb": "Air Waybill air freight document cargo",
    "hawb": "House Air Waybill air freight forwarder",
    "mawb": "Master Air Waybill air freight airline",
    "uld": "Unit Load Device air cargo container pallet",
    "gsa": "General Sales Agent airline freight sales",
    "bco": "Beneficial Cargo Owner shipper direct",
    "nvocc": "Non-Vessel Operating Common Carrier forwarder ocean freight",
    # Technology
    "edi": "Electronic Data Interchange customs trade documents",
    "tms": "Transportation Management System logistics software",
    "wms": "Warehouse Management System inventory logistics",
    "erp": "Enterprise Resource Planning supply chain system",
    # Carriers (when abbreviated)
    "cma": "CMA CGM carrier container shipping line",
    "oocl": "Orient Overseas Container Line carrier shipping",
    "one": "Ocean Network Express carrier container shipping",
    "hmm": "Hyundai Merchant Marine carrier container shipping",
    "zim": "ZIM Integrated Shipping carrier container line",
    "pil": "Pacific International Lines carrier shipping",
    "hl": "Hapag-Lloyd carrier container shipping line",
    # Alliances
    "2m": "2M Alliance Maersk MSC carrier ocean shipping",
    "the alliance": "THE Alliance Hapag ONE HMM Yang Ming carrier ocean shipping",
    "ocean alliance": "Ocean Alliance CMA COSCO Evergreen OOCL carrier ocean shipping",
    "gemini": "Gemini Cooperation Maersk Hapag-Lloyd carrier alliance",
}

# ── Entity Recognition Patterns ─────────────────────────────────────────────
# Detects multi-word logistics entities not in the acronym table

ENTITY_EXPANSIONS: list[tuple[str, str]] = [
    (r"\bblank\s*sail(?:ing)?s?\b", "blank sailing carrier capacity reduction vessel"),
    (r"\bport\s*strike\b", "port strike dock workers labor disruption congestion"),
    (r"\bdock\s*strike\b", "dock strike longshoremen labor disruption port"),
    (r"\bwork\s*stoppage\b", "work stoppage labor strike port disruption"),
    (r"\bslow\s*(?:down|steam(?:ing)?)\b", "slow steaming fuel saving vessel delay"),
    (r"\bblack\s*swan\b", "black swan unexpected disruption catastrophic event"),
    (r"\bforce\s*majeure\b", "force majeure disruption unforeseeable event shipping"),
    (r"\bvoid(?:ed)?\s*sail(?:ing)?s?\b", "voided sailing cancelled vessel capacity blank"),
    (r"\bwar\s*risk\b", "war risk insurance premium maritime security conflict"),
    (r"\bpiracy\b", "piracy maritime security vessel attack threat"),
    (r"\broute\s*deviation\b", "route deviation rerouting cape of good hope longer transit"),
    (r"\bcape\s*(?:of\s*)?good\s*hope\b", "Cape of Good Hope route deviation rerouting africa"),
]

# ── Transport Mode Hints ──────────────────────────────────────────────────
# Explicit mode keywords to inject into expanded query for metadata filtering

MODE_KEYWORDS: dict[str, list[str]] = {
    "ocean": [
        "ocean", "sea", "maritime", "vessel", "container ship", "tanker",
        "bulk carrier", "port", "berth", "anchorage", "teu", "feu",
        "sea-air", "sea air",  # cross-domain triggers
    ],
    "air": [
        "air freight", "air cargo", "airline", "aircraft", "belly cargo",
        "freighter", "airport", "iata", "awb", "uld",
        "sea-air", "sea air", "air-sea",  # cross-domain triggers
    ],
    "rail": [
        "rail", "railway", "intermodal", "train", "railcar",
        "block train", "china-europe", "land bridge",
    ],
    "road": [
        "truck", "trucking", "drayage", "road", "highway",
        "chassis", "trailer", "last mile",
    ],
}

# ── Cross-domain conversion patterns ──────────────────────────────────────
# Phrases that explicitly indicate multi-modal scenarios.
# Used by detect_transport_modes() to force secondary mode detection even
# when keyword counts are lopsided.

CROSS_DOMAIN_PATTERNS: list[tuple[str, list[str]]] = [
    (r"sea[\s-]air|air[\s-]sea", ["ocean", "air"]),
    (r"rail[\s-]sea|sea[\s-]rail", ["ocean", "rail"]),
    (r"truck[\s-](?:to[\s-])?rail|rail[\s-](?:to[\s-])?truck|road[\s-]rail|rail[\s-]road", ["rail", "road"]),
    (r"air[\s-](?:to[\s-])?road|road[\s-](?:to[\s-])?air", ["air", "road"]),
    (r"\bintermodal\b", ["rail", "road"]),
]


def expand_query(query: str) -> str:
    """Expand a user query with ontology context.

    1. Resolve acronyms to full forms + context keywords
    2. Detect multi-word entities and inject context
    3. Return expanded query for both intent classification and embedding

    Original query is always preserved at the front.
    """
    query_lower = query.lower()
    expansions: list[str] = []

    # Step 1: Acronym resolution
    # Tokenize and match whole words only
    words = re.findall(r"\b[\w/]+\b", query_lower)
    seen_expansions: set[str] = set()

    for word in words:
        if word in ACRONYM_ONTOLOGY and word not in seen_expansions:
            expansions.append(ACRONYM_ONTOLOGY[word])
            seen_expansions.add(word)

    # Also try bigrams for multi-word acronyms (e.g., "eu ets")
    for i in range(len(words) - 1):
        bigram = f"{words[i]} {words[i + 1]}"
        if bigram in ACRONYM_ONTOLOGY and bigram not in seen_expansions:
            expansions.append(ACRONYM_ONTOLOGY[bigram])
            seen_expansions.add(bigram)

    # Step 2: Entity pattern expansion
    for pattern, expansion in ENTITY_EXPANSIONS:
        if re.search(pattern, query_lower):
            expansions.append(expansion)

    if not expansions:
        return query

    expanded = f"{query} [{' | '.join(expansions)}]"
    return expanded


def detect_transport_mode(query: str) -> str | None:
    """Detect *primary* transport mode from query text.

    Returns: 'ocean', 'air', 'rail', 'road', or None.
    Kept for backward compatibility — prefer ``detect_transport_modes`` for
    cross-domain queries.
    """
    modes = detect_transport_modes(query)
    return modes[0] if modes else None


def detect_transport_modes(query: str) -> list[str]:
    """Detect **all** transport modes present in the query.

    Returns a list of detected modes sorted by relevance score (highest first).
    An empty list means no specific mode was detected.

    This powers the Multi-Modal Query Decomposition:
      "Red Sea vessel diversions forcing sea-air conversion at Dubai"
      → ["ocean", "air"]
    """
    query_lower = query.lower()
    mode_scores: dict[str, int] = {}

    for mode, keywords in MODE_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in query_lower:
                score += 1
        if score > 0:
            mode_scores[mode] = score

    # Cross-domain patterns: force-inject modes that explicit conversion
    # phrases imply, even if keyword counts alone wouldn't detect them.
    for pattern, forced_modes in CROSS_DOMAIN_PATTERNS:
        if re.search(pattern, query_lower):
            for mode in forced_modes:
                if mode not in mode_scores:
                    mode_scores[mode] = 1  # minimum score to include

    if not mode_scores:
        return []

    # Return all detected modes, sorted by score descending
    return sorted(mode_scores, key=lambda k: mode_scores[k], reverse=True)
