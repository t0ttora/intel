"""Keyword gate (regex) — multimodal logistics: ocean, air, rail, road, cyber, macro, geoint."""
from __future__ import annotations

import re

# ── Multimodal logistics keyword filter ──────────────────────────────────
# Covers ocean, air, rail, road, cyber, macro, geoint, and cross-cutting
# supply chain terms. A signal must match at least one keyword to pass.

LOGISTICS_KEYWORDS = re.compile(
    r"(?i)\b("
    # Ocean / Maritime
    r"port|freight|container|vessel|shipping|logistics|cargo|TEU|FEU|"
    r"maritime|tanker|bulk|carrier|maersk|msc|cma.?cgm|hapag|cosco|evergreen|"
    r"suez|panama|malacca|hormuz|bab.?el.?mandeb|rotterdam|hamburg|shanghai|singapore|"
    r"AIS|dwell.?time|blank.?sailing|reroute|congestion|delay|strike|blockade|"
    r"berth|anchorage|draft.?restriction|demurrage|detention|stevedore|longshor|"
    r"nvocc|fcl|lcl|bill.?of.?lading|"
    r"vessel.?turnaround|chassis.?pool|container.?imbalance|equipment.?repositioning|"
    r"feeder.?service|transshipment|hub.?port|bunker.?surcharge|"
    # Air Cargo
    r"air.?freight|air.?cargo|belly.?cargo|freighter.?aircraft|"
    r"airline|aircraft|airport|runway|tarmac|"
    r"iata|awb|air.?waybill|hawb|mawb|uld|"
    r"cargo.?plane|wide.?body|charter.?flight|"
    r"gsa|general.?sales.?agent|bafi|tact.?rate|"
    r"a.?cdm|ground.?handling|"
    r"freighter.?conversion|p2f|load.?factor|chargeable.?weight|"
    r"pharma.?cold.?chain|perishable.?cargo|temp.?controlled|"
    r"tac.?index|worldacd|clive.?data|"
    # Rail / Intermodal
    r"rail.?freight|railway|railroad|intermodal|"
    r"block.?train|unit.?train|trainload|"
    r"china.?europe.?rail|land.?bridge|trans.?siberian|"
    r"rail.?terminal|marshalling.?yard|locomotive|"
    r"union.?pacific|bnsf|csx|norfolk.?southern|cn.?rail|cp.?rail|"
    r"db.?schenker|db.?cargo|"
    r"intermodal.?ramp|railcar.?shortage|car.?supply|"
    r"psr|precision.?scheduled|double.?stack|well.?car|"
    # Road / Trucking
    r"trucking|drayage|road.?freight|road.?transport|"
    r"chassis|trailer|flatbed|reefer.?truck|"
    r"last.?mile|first.?mile|cross.?dock|"
    r"driver.?shortage|hours.?of.?service|"
    r"spot.?rate|deadhead|dead.?head|empty.?miles|"
    r"detention.?time|lumper.?fee|accessorial|"
    r"eld.?mandate|electronic.?logging|"
    r"ltl|less.?than.?truckload|ftl|full.?truckload|"
    r"dat.?load.?board|load.?board|fuel.?surcharge|"
    # Pricing / Indices
    r"SCFI|WCI|freightos|drewry|FBX|BDI|"
    r"TAC.?index|xeneta|freight.?index|"
    r"rate.?hike|rate.?surge|surcharge|GRI|"
    # Regulatory / Customs
    r"IMO|UKMTO|customs|tariff|embargo|sanctions|"
    r"hazmat|dangerous.?goods|lithium.?battery|"
    r"cbp|border.?force|DG.?TAXUD|"
    r"fmc|fmcsa|stb|surface.?transportation|"
    # Cyber / Risk Intelligence
    r"ransomware|malware|cyberattack|cyber.?attack|"
    r"data.?breach|phishing|scada|ics.?cert|"
    r"gps.?spoofing|ais.?spoofing|"
    r"operational.?technology|ot.?security|"
    r"supply.?chain.?attack|software.?supply.?chain|"
    # Macro / Economic
    r"reshoring|nearshoring|friend.?shoring|onshoring|"
    r"trade.?war|tariff.?war|retaliatory.?tariff|"
    r"inventory.?glut|demand.?soften|order.?cancel|"
    r"pmi|purchasing.?managers|manufacturing.?index|"
    r"import.?volume|export.?control|entity.?list|"
    # GEOINT / Weather / Satellite
    r"wildfire|satellite.?imagery|crop.?failure|drought|"
    r"nasa.?firms|sentinel.?hub|modis|viirs|"
    r"volcanic.?ash|ash.?cloud|notam|sigmet|"
    # Cross-cutting disruption signals
    r"supply.?chain|disruption|bottleneck|capacity|"
    r"hurricane|typhoon|cyclone|storm|earthquake|flood|"
    r"derailment|grounding|collision|fire"
    r")\b"
)


def passes_keyword_filter(text: str) -> bool:
    """Return True if the text matches at least one logistics keyword."""
    return bool(LOGISTICS_KEYWORDS.search(text))


def count_keyword_matches(text: str) -> int:
    """Count the number of unique keyword matches in the text."""
    matches = LOGISTICS_KEYWORDS.findall(text)
    return len(set(m.lower() for m in matches))
