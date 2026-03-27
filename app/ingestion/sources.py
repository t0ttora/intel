"""Central source registry — single source of truth for all data feeds.

Every source has structured metadata: tier, mode, source_type, reliability.
This feeds into the ingestion pipeline so every signal gets tagged correctly
at the point of entry, eliminating cross-domain contamination.

Tiers:
    1 — Every 15 min: live physical data, terminal gates, pricing APIs
    2 — Every 1 hour: tier-1 news, chokepoint status
    3 — Every 5-10 min (FILTERED): social/forum intelligence
    4 — Daily: regulations, customs, embargoes
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Source:
    """A single data source with full metadata."""

    name: str
    url: str
    source_key: str
    source_type: str  # news, official, social, physical, pricing, api, cyber, geoint
    tier: int  # 1-4
    modes: list[str] = field(default_factory=lambda: ["ocean"])
    reliability: float = 0.5
    # For social sources: keyword filter required
    requires_keyword_filter: bool = False
    # Whether the source needs Playwright (JS-rendered)
    needs_playwright: bool = False
    # For API sources: which env var holds the key
    api_key_env: str | None = None
    # Ingestion method hint: rss, api, playwright, bs4
    ingestion_method: str = "rss"


# ═══════════════════════════════════════════════════════════════════════════
#  TIER 1 — LIVE DATA FEEDS (every 15 min)
# ═══════════════════════════════════════════════════════════════════════════

TIER1_LIVE_FEEDS: list[Source] = [
    # ── Port Authorities (AIS/Gate data) ─────────────────────────────────
    Source(
        name="Port of Los Angeles — Signal",
        url="https://www.portoflosangeles.org/references/news_newsfeed.xml",
        source_key="port_la",
        source_type="official",
        tier=1,
        modes=["ocean"],
        reliability=0.95,
        ingestion_method="rss",
    ),
    Source(
        name="Port of Long Beach",
        url="https://polb.com/feed/",
        source_key="port_long_beach",
        source_type="official",
        tier=1,
        modes=["ocean"],
        reliability=0.95,
        ingestion_method="rss",
    ),
    Source(
        name="Port of Rotterdam",
        url="https://www.portofrotterdam.com/en/news/rss",
        source_key="port_rotterdam",
        source_type="official",
        tier=1,
        modes=["ocean", "rail", "road"],
        reliability=0.95,
        ingestion_method="rss",
    ),
    Source(
        name="Maritime and Port Authority of Singapore",
        url="https://www.mpa.gov.sg/media-centre/rss",
        source_key="port_singapore",
        source_type="official",
        tier=1,
        modes=["ocean"],
        reliability=0.95,
        ingestion_method="rss",
    ),
    Source(
        name="Port of Shanghai (SIPG)",
        url="https://www.portshanghai.com.cn/en/news.html",
        source_key="port_shanghai",
        source_type="official",
        tier=1,
        modes=["ocean"],
        reliability=0.9,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    Source(
        name="Port of Hamburg",
        url="https://www.hafen-hamburg.de/en/feed/",
        source_key="port_hamburg",
        source_type="official",
        tier=1,
        modes=["ocean", "rail"],
        reliability=0.9,
        ingestion_method="rss",
    ),
    Source(
        name="Port of Antwerp-Bruges",
        url="https://newsroom.portofantwerpbruges.com/rss",
        source_key="port_antwerp",
        source_type="official",
        tier=1,
        modes=["ocean", "rail", "road"],
        reliability=0.9,
        ingestion_method="rss",
    ),
    # ── Pricing — Live APIs ──────────────────────────────────────────────
    Source(
        name="Baltic Exchange (Dry Index)",
        url="https://www.balticexchange.com/en/data-services/market-information.html",
        source_key="baltic_exchange",
        source_type="pricing",
        tier=1,
        modes=["ocean"],
        reliability=0.95,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    Source(
        name="Freightos FBX Live",
        url="https://fbx.freightos.com/",
        source_key="freightos_fbx_live",
        source_type="pricing",
        tier=1,
        modes=["ocean"],
        reliability=0.9,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    Source(
        name="TAC Index (Air Cargo Rates)",
        url="https://www.tacindex.com/",
        source_key="tac_index",
        source_type="pricing",
        tier=1,
        modes=["air"],
        reliability=0.9,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    Source(
        name="DAT Freight & Analytics",
        url="https://www.dat.com/industry-trends/trendlines",
        source_key="dat_freight",
        source_type="pricing",
        tier=1,
        modes=["road"],
        reliability=0.9,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    # ── Tracking / Visibility Platforms ───────────────────────────────────
    Source(
        name="Project44 — Supply Chain Visibility",
        url="https://www.project44.com/blog/feed",
        source_key="project44",
        source_type="news",
        tier=1,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.85,
        ingestion_method="rss",
    ),
    Source(
        name="FourKites — Visibility Intel",
        url="https://www.fourkites.com/blog/feed/",
        source_key="fourkites",
        source_type="news",
        tier=1,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.85,
        ingestion_method="rss",
    ),
    # ── Decision Engine v1.0 — Verified Catalog Sources ──────────────────
    Source(
        name="Port of New York/New Jersey (PANYNJ)",
        url="https://www.panynj.gov/port-authority/en/press-room.html",
        source_key="port_nynj",
        source_type="official",
        tier=1,
        modes=["ocean"],
        reliability=0.95,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    Source(
        name="JAXPORT (Jacksonville)",
        url="https://www.jaxport.com/feed/",
        source_key="port_jaxport",
        source_type="official",
        tier=1,
        modes=["ocean"],
        reliability=0.90,
        ingestion_method="rss",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════
#  TIER 1 — CYBER / RISK INTELLIGENCE (every 15 min)
# ═══════════════════════════════════════════════════════════════════════════

TIER1_CYBER_FEEDS: list[Source] = [
    Source(
        name="CISA Alerts",
        url="https://www.cisa.gov/cybersecurity-advisories/all.xml",
        source_key="cisa_alerts",
        source_type="cyber",
        tier=1,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.95,
        ingestion_method="rss",
    ),
    Source(
        name="ICS-CERT Advisories",
        url="https://www.cisa.gov/uscert/ics/advisories/advisories.xml",
        source_key="ics_cert",
        source_type="cyber",
        tier=1,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.95,
        ingestion_method="rss",
    ),
    Source(
        name="BleepingComputer",
        url="https://www.bleepingcomputer.com/feed/",
        source_key="bleepingcomputer",
        source_type="cyber",
        tier=1,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.7,
        requires_keyword_filter=True,
        ingestion_method="rss",
    ),
    Source(
        name="DarkReading",
        url="https://www.darkreading.com/rss.xml",
        source_key="darkreading",
        source_type="cyber",
        tier=1,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.7,
        requires_keyword_filter=True,
        ingestion_method="rss",
    ),
    Source(
        name="The Record by Recorded Future",
        url="https://therecord.media/feed",
        source_key="recorded_future",
        source_type="cyber",
        tier=1,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.8,
        requires_keyword_filter=True,
        ingestion_method="rss",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════
#  TIER 1 — GEOINT / WEATHER / SATELLITE (every 15 min)
# ═══════════════════════════════════════════════════════════════════════════

TIER1_GEOINT_FEEDS: list[Source] = [
    Source(
        name="NASA FIRMS — Active Fire Data",
        url="https://firms.modaps.eosdis.nasa.gov/api/area/csv",
        source_key="nasa_firms",
        source_type="geoint",
        tier=1,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.95,
        api_key_env="NASA_FIRMS_API_KEY",
        ingestion_method="api",
    ),
    Source(
        name="Copernicus Sentinel Hub",
        url="https://services.sentinel-hub.com/api/v1/",
        source_key="sentinel_hub",
        source_type="geoint",
        tier=1,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.9,
        api_key_env="SENTINEL_HUB_KEY",
        ingestion_method="api",
    ),
    Source(
        name="Windy — Severe Weather",
        url="https://api.windy.com/api/webcams/v3/",
        source_key="windy",
        source_type="geoint",
        tier=1,
        modes=["ocean", "air", "multimodal"],
        reliability=0.85,
        api_key_env="WINDY_API_KEY",
        ingestion_method="api",
    ),
    Source(
        name="OpenSky Network — ADS-B",
        url="https://opensky-network.org/api/states/all",
        source_key="opensky",
        source_type="geoint",
        tier=1,
        modes=["air"],
        reliability=0.85,
        ingestion_method="api",
    ),
    Source(
        name="FlightRadar24 — Disruptions",
        url="https://www.flightradar24.com/blog/feed/",
        source_key="flightradar24",
        source_type="geoint",
        tier=1,
        modes=["air"],
        reliability=0.8,
        ingestion_method="rss",
    ),
    Source(
        name="MarineTraffic News",
        url="https://www.marinetraffic.com/blog/feed/",
        source_key="marinetraffic",
        source_type="geoint",
        tier=1,
        modes=["ocean"],
        reliability=0.85,
        ingestion_method="rss",
    ),
    Source(
        name="VesselFinder News",
        url="https://www.vesselfinder.com/news/rss",
        source_key="vesselfinder",
        source_type="geoint",
        tier=1,
        modes=["ocean"],
        reliability=0.8,
        ingestion_method="rss",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════
#  TIER 2 — NEWS RSS FEEDS (every 1 hour)
# ═══════════════════════════════════════════════════════════════════════════

TIER2_NEWS_FEEDS: list[Source] = [
    # ── Ocean / Maritime ─────────────────────────────────────────────────
    Source(
        name="Lloyd's List",
        url="https://lloydslist.maritimeintelligence.informa.com/rss",
        source_key="lloyds_list",
        source_type="news",
        tier=2,
        modes=["ocean"],
        reliability=0.9,
        ingestion_method="rss",
    ),
    Source(
        name="TradeWinds",
        url="https://www.tradewindsnews.com/rss",
        source_key="tradewinds",
        source_type="news",
        tier=2,
        modes=["ocean"],
        reliability=0.85,
        ingestion_method="rss",
    ),
    Source(
        name="gCaptain",
        url="https://gcaptain.com/feed/",
        source_key="gcaptain",
        source_type="news",
        tier=2,
        modes=["ocean"],
        reliability=0.8,
        ingestion_method="rss",
    ),
    Source(
        name="Splash247",
        url="https://splash247.com/feed/",
        source_key="splash247",
        source_type="news",
        tier=2,
        modes=["ocean"],
        reliability=0.75,
        ingestion_method="rss",
    ),
    Source(
        name="Maritime Executive",
        url="https://maritime-executive.com/rss",
        source_key="maritime_executive",
        source_type="news",
        tier=2,
        modes=["ocean"],
        reliability=0.75,
        ingestion_method="rss",
    ),
    Source(
        name="Hellenic Shipping News",
        url="https://www.hellenicshippingnews.com/feed/",
        source_key="hellenic_shipping",
        source_type="news",
        tier=2,
        modes=["ocean"],
        reliability=0.7,
        ingestion_method="rss",
    ),
    Source(
        name="Seatrade Maritime",
        url="https://www.seatrade-maritime.com/rss.xml",
        source_key="seatrade",
        source_type="news",
        tier=2,
        modes=["ocean"],
        reliability=0.75,
        ingestion_method="rss",
    ),
    Source(
        name="Alphaliner",
        url="https://alphaliner.axsmarine.com/PublicTop100/",
        source_key="alphaliner",
        source_type="news",
        tier=2,
        modes=["ocean"],
        reliability=0.9,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    Source(
        name="BIMCO — Market Analysis",
        url="https://www.bimco.org/news-and-trends",
        source_key="bimco",
        source_type="news",
        tier=2,
        modes=["ocean"],
        reliability=0.9,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    Source(
        name="Sea-Intelligence",
        url="https://sea-intelligence.com/press-room",
        source_key="sea_intelligence",
        source_type="news",
        tier=2,
        modes=["ocean"],
        reliability=0.9,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    Source(
        name="Port Technology International",
        url="https://www.porttechnology.org/feed/",
        source_key="port_tech_intl",
        source_type="news",
        tier=2,
        modes=["ocean"],
        reliability=0.8,
        ingestion_method="rss",
    ),
    Source(
        name="Container News",
        url="https://container-news.com/feed/",
        source_key="container_news",
        source_type="news",
        tier=2,
        modes=["ocean"],
        reliability=0.75,
        ingestion_method="rss",
    ),
    # ── Air Cargo ────────────────────────────────────────────────────────
    Source(
        name="Air Cargo News",
        url="https://www.aircargonews.net/feed/",
        source_key="aircargo_news",
        source_type="news",
        tier=2,
        modes=["air"],
        reliability=0.85,
        ingestion_method="rss",
    ),
    Source(
        name="The Loadstar",
        url="https://theloadstar.com/feed/",
        source_key="loadstar",
        source_type="news",
        tier=2,
        modes=["ocean", "air", "multimodal"],
        reliability=0.85,
        ingestion_method="rss",
    ),
    Source(
        name="Air Cargo World",
        url="https://aircargoworld.com/feed/",
        source_key="aircargo_world",
        source_type="news",
        tier=2,
        modes=["air"],
        reliability=0.8,
        ingestion_method="rss",
    ),
    Source(
        name="FlightGlobal Cargo",
        url="https://www.flightglobal.com/rss",
        source_key="flightglobal",
        source_type="news",
        tier=2,
        modes=["air"],
        reliability=0.8,
        ingestion_method="rss",
    ),
    Source(
        name="Cargo Facts",
        url="https://cargofacts.com/feed/",
        source_key="cargo_facts",
        source_type="news",
        tier=2,
        modes=["air"],
        reliability=0.8,
        ingestion_method="rss",
    ),
    Source(
        name="STAT Trade Times",
        url="https://www.stattimes.com/feed/",
        source_key="stat_trade_times",
        source_type="news",
        tier=2,
        modes=["air"],
        reliability=0.8,
        ingestion_method="rss",
    ),
    Source(
        name="Payload Asia",
        url="https://www.payloadasia.com/feed/",
        source_key="payload_asia",
        source_type="news",
        tier=2,
        modes=["air"],
        reliability=0.75,
        ingestion_method="rss",
    ),
    Source(
        name="Simple Flying — Cargo",
        url="https://simpleflying.com/feed/",
        source_key="simple_flying",
        source_type="news",
        tier=2,
        modes=["air"],
        reliability=0.65,
        requires_keyword_filter=True,
        ingestion_method="rss",
    ),
    Source(
        name="Airport Council International",
        url="https://aci.aero/feed/",
        source_key="aci_aero",
        source_type="official",
        tier=2,
        modes=["air"],
        reliability=0.9,
        ingestion_method="rss",
    ),
    # ── Rail / Intermodal ────────────────────────────────────────────────
    Source(
        name="RailFreight.com",
        url="https://www.railfreight.com/feed/",
        source_key="railfreight_com",
        source_type="news",
        tier=2,
        modes=["rail"],
        reliability=0.85,
        ingestion_method="rss",
    ),
    Source(
        name="Railway Age",
        url="https://www.railwayage.com/feed/",
        source_key="railway_age",
        source_type="news",
        tier=2,
        modes=["rail"],
        reliability=0.75,
        ingestion_method="rss",
    ),
    Source(
        name="International Railway Journal",
        url="https://www.railjournal.com/feed/",
        source_key="irj",
        source_type="news",
        tier=2,
        modes=["rail"],
        reliability=0.85,
        ingestion_method="rss",
    ),
    Source(
        name="UIC — International Union of Railways",
        url="https://uic.org/com/enews/",
        source_key="uic",
        source_type="official",
        tier=2,
        modes=["rail"],
        reliability=0.9,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    # ── Multimodal / Cross-cutting ───────────────────────────────────────
    Source(
        name="Freightwaves",
        url="https://www.freightwaves.com/feed",
        source_key="freightwaves",
        source_type="news",
        tier=2,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.8,
        ingestion_method="rss",
    ),
    Source(
        name="Journal of Commerce",
        url="https://www.joc.com/rss",
        source_key="joc",
        source_type="news",
        tier=2,
        modes=["ocean", "rail", "multimodal"],
        reliability=0.9,
        ingestion_method="rss",
    ),
    Source(
        name="Supply Chain Dive",
        url="https://www.supplychaindive.com/feeds/news/",
        source_key="supplychaindive",
        source_type="news",
        tier=2,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.75,
        ingestion_method="rss",
    ),
    Source(
        name="Reuters — Supply Chain",
        url="https://www.reuters.com/arc/outboundfeeds/rss/category/supply-chain/",
        source_key="reuters_supply_chain",
        source_type="news",
        tier=2,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.95,
        ingestion_method="rss",
    ),
    Source(
        name="Bloomberg Supply Chain",
        url="https://www.bloomberg.com/feed/supply-chain",
        source_key="bloomberg_supply_chain",
        source_type="news",
        tier=2,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.95,
        ingestion_method="rss",
    ),
    # ── Road / Trucking ──────────────────────────────────────────────────
    Source(
        name="Transport Topics",
        url="https://www.ttnews.com/rss.xml",
        source_key="transport_topics",
        source_type="news",
        tier=2,
        modes=["road"],
        reliability=0.8,
        ingestion_method="rss",
    ),
    Source(
        name="Overdrive Online",
        url="https://www.overdriveonline.com/feed/",
        source_key="overdrive",
        source_type="news",
        tier=2,
        modes=["road"],
        reliability=0.7,
        ingestion_method="rss",
    ),
    Source(
        name="FleetOwner",
        url="https://www.fleetowner.com/rss",
        source_key="fleetowner",
        source_type="news",
        tier=2,
        modes=["road"],
        reliability=0.75,
        ingestion_method="rss",
    ),
    Source(
        name="IRU — International Road Transport Union",
        url="https://www.iru.org/news-resources/newsroom",
        source_key="iru",
        source_type="official",
        tier=2,
        modes=["road"],
        reliability=0.9,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    Source(
        name="Commercial Carrier Journal",
        url="https://www.ccjdigital.com/feed/",
        source_key="ccj",
        source_type="news",
        tier=2,
        modes=["road"],
        reliability=0.7,
        ingestion_method="rss",
    ),
    # ── Decision Engine v1.0 — Verified Catalog Sources ──────────────────
    Source(
        name="Ship Technology",
        url="https://www.ship-technology.com/feed/",
        source_key="ship_technology",
        source_type="news",
        tier=2,
        modes=["ocean"],
        reliability=0.75,
        ingestion_method="rss",
    ),
    Source(
        name="Offshore Energy",
        url="https://www.offshore-energy.biz/feed/",
        source_key="offshore_energy",
        source_type="news",
        tier=2,
        modes=["ocean"],
        reliability=0.80,
        ingestion_method="rss",
    ),
    Source(
        name="Maritime Professional",
        url="https://www.maritimeprofessional.com/rss",
        source_key="maritime_professional",
        source_type="news",
        tier=2,
        modes=["ocean"],
        reliability=0.80,
        ingestion_method="rss",
    ),
    Source(
        name="SAFETY4SEA",
        url="https://safety4sea.com/feed/",
        source_key="safety4sea",
        source_type="news",
        tier=2,
        modes=["ocean"],
        reliability=0.80,
        ingestion_method="rss",
    ),
    Source(
        name="DC Velocity",
        url="https://www.dcvelocity.com/rss/",
        source_key="dc_velocity",
        source_type="news",
        tier=2,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.80,
        ingestion_method="rss",
    ),
    Source(
        name="Ship.Energy (Bunkerspot)",
        url="https://ship.energy/rss",
        source_key="ship_energy",
        source_type="news",
        tier=2,
        modes=["ocean"],
        reliability=0.75,
        ingestion_method="rss",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════
#  TIER 2 — CHOKEPOINT & WEATHER (every 1 hour)
# ═══════════════════════════════════════════════════════════════════════════

TIER2_CHOKEPOINT_FEEDS: list[Source] = [
    Source(
        name="UKMTO Maritime Security",
        url="https://www.ukmto.org/recent-incidents",
        source_key="ukmto",
        source_type="official",
        tier=2,
        modes=["ocean"],
        reliability=0.95,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    Source(
        name="NOAA Active Alerts",
        url="https://api.weather.gov/alerts/active",
        source_key="noaa_alerts",
        source_type="official",
        tier=2,
        modes=["ocean", "air", "multimodal"],
        reliability=0.95,
        ingestion_method="api",
    ),
    Source(
        name="GDACS Disaster Alerts",
        url="https://www.gdacs.org/xml/rss.xml",
        source_key="gdacs",
        source_type="official",
        tier=2,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.95,
        ingestion_method="rss",
    ),
    Source(
        name="ReliefWeb — Disasters",
        url="https://reliefweb.int/updates/rss.xml?content-format=report&primary_country=world",
        source_key="reliefweb",
        source_type="official",
        tier=2,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.9,
        requires_keyword_filter=True,
        ingestion_method="rss",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════
#  TIER 2 — PRICING & INDEX (every 1 hour)
# ═══════════════════════════════════════════════════════════════════════════

TIER2_PRICING_FEEDS: list[Source] = [
    Source(
        name="Freightos Blog (FBX Index)",
        url="https://www.freightos.com/blog/feed/",
        source_key="freightos_fbx",
        source_type="pricing",
        tier=2,
        modes=["ocean"],
        reliability=0.85,
        ingestion_method="rss",
    ),
    Source(
        name="Xeneta Updates",
        url="https://www.xeneta.com/blog/rss.xml",
        source_key="xeneta",
        source_type="pricing",
        tier=2,
        modes=["ocean", "air"],
        reliability=0.85,
        ingestion_method="rss",
    ),
    Source(
        name="Drewry Shipping Consultants",
        url="https://www.drewry.co.uk/feed",
        source_key="drewry",
        source_type="pricing",
        tier=2,
        modes=["ocean"],
        reliability=0.9,
        ingestion_method="rss",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════
#  TIER 2 — MACRO / ECONOMIC INTELLIGENCE (every 1 hour)
# ═══════════════════════════════════════════════════════════════════════════

TIER2_MACRO_FEEDS: list[Source] = [
    Source(
        name="IMF — Data API",
        url="https://www.imf.org/en/News/rss",
        source_key="imf",
        source_type="official",
        tier=2,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.95,
        requires_keyword_filter=True,
        ingestion_method="rss",
    ),
    Source(
        name="World Bank — Trade Data",
        url="https://blogs.worldbank.org/feed",
        source_key="world_bank",
        source_type="official",
        tier=2,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.95,
        requires_keyword_filter=True,
        ingestion_method="rss",
    ),
    Source(
        name="WTO — Trade News",
        url="https://www.wto.org/english/news_e/news_e.rss",
        source_key="wto",
        source_type="official",
        tier=2,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.95,
        ingestion_method="rss",
    ),
    Source(
        name="UN Comtrade — Trade Statistics",
        url="https://comtradeapi.un.org/public/v1/preview/C/A/HS",
        source_key="un_comtrade",
        source_type="api",
        tier=2,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.95,
        api_key_env="UN_COMTRADE_KEY",
        ingestion_method="api",
    ),
    Source(
        name="UNCTAD — Trade & Development",
        url="https://unctad.org/rss.xml",
        source_key="unctad",
        source_type="official",
        tier=2,
        modes=["ocean", "air", "multimodal"],
        reliability=0.9,
        requires_keyword_filter=True,
        ingestion_method="rss",
    ),
    Source(
        name="OECD — Trade Policy",
        url="https://www.oecd.org/trade/rss/",
        source_key="oecd_trade",
        source_type="official",
        tier=2,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.9,
        requires_keyword_filter=True,
        ingestion_method="rss",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════
#  TIER 3 — SOCIAL / HUMAN INTELLIGENCE (every 5 min, KEYWORD-FILTERED)
# ═══════════════════════════════════════════════════════════════════════════

# Impact keywords for social signal filtering — only ingest posts that match
SOCIAL_IMPACT_KEYWORDS = (
    r"(?i)\b("
    r"delay|delayed|delays|"
    r"strike|strikes|striking|walkout|"
    r"congestion|congested|"
    r"overload|overloaded|backlog|backed\s*up|"
    r"reroute|rerouted|rerouting|diversion|diverted|"
    r"blank\s*sailing|cancelled|canceled|"
    r"chassis\s*shortage|equipment\s*shortage|"
    r"customs\s*stuck|customs\s*hold|customs\s*delay|"
    r"gate\s*overloaded|gate\s*closed|gate\s*congestion|"
    r"embargo|embargoed|"
    r"hurricane|typhoon|cyclone|storm\s*warning|"
    r"grounding|capsiz|collision|fire\s*on\s*board|"
    r"port\s*closure|port\s*closed|terminal\s*closed|"
    r"capacity\s*crunch|space\s*shortage|"
    r"rate\s*hike|rate\s*surge|surcharge|"
    r"trucker?\s*shortage|driver\s*shortage|"
    r"rail\s*embargo|rail\s*disruption|derailment|"
    r"ransomware|cyberattack|data\s*breach|"
    r"reshoring|nearshoring|friend.?shoring|"
    r"tariff\s*war|trade\s*war|sanction"
    r")\b"
)

TIER3_SOCIAL_SOURCES: list[Source] = [
    Source(
        name="Reddit r/logistics",
        url="https://www.reddit.com/r/logistics/new.json?limit=50",
        source_key="reddit_logistics",
        source_type="social",
        tier=3,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.35,
        requires_keyword_filter=True,
        ingestion_method="api",
    ),
    Source(
        name="Reddit r/freightforwarding",
        url="https://www.reddit.com/r/FreightForwarding/new.json?limit=50",
        source_key="reddit_freight",
        source_type="social",
        tier=3,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.35,
        requires_keyword_filter=True,
        ingestion_method="api",
    ),
    Source(
        name="Reddit r/supplychain",
        url="https://www.reddit.com/r/supplychain/new.json?limit=50",
        source_key="reddit_supplychain",
        source_type="social",
        tier=3,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.3,
        requires_keyword_filter=True,
        ingestion_method="api",
    ),
    Source(
        name="Reddit r/shipping",
        url="https://www.reddit.com/r/shipping/new.json?limit=50",
        source_key="reddit_shipping",
        source_type="social",
        tier=3,
        modes=["ocean", "road"],
        reliability=0.3,
        requires_keyword_filter=True,
        ingestion_method="api",
    ),
    Source(
        name="Reddit r/truckers",
        url="https://www.reddit.com/r/Truckers/new.json?limit=50",
        source_key="reddit_truckers",
        source_type="social",
        tier=3,
        modes=["road"],
        reliability=0.3,
        requires_keyword_filter=True,
        ingestion_method="api",
    ),
    Source(
        name="Reddit r/aviationmaintenance",
        url="https://www.reddit.com/r/aviationmaintenance/new.json?limit=50",
        source_key="reddit_aviation",
        source_type="social",
        tier=3,
        modes=["air"],
        reliability=0.25,
        requires_keyword_filter=True,
        ingestion_method="api",
    ),
    Source(
        name="Reddit r/freightbrokers",
        url="https://www.reddit.com/r/FreightBrokers/new.json?limit=50",
        source_key="reddit_freightbrokers",
        source_type="social",
        tier=3,
        modes=["road", "multimodal"],
        reliability=0.35,
        requires_keyword_filter=True,
        ingestion_method="api",
    ),
    Source(
        name="Hacker News — Logistics/Supply Chain",
        url="https://hn.algolia.com/api/v1/search_by_date",
        source_key="hackernews",
        source_type="social",
        tier=3,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.4,
        requires_keyword_filter=True,
        ingestion_method="api",
    ),
]

# ═══════════════════════════════════════════════════════════════════════════
#  TIER 4 — REGULATORY / INSTITUTIONAL (daily)
# ═══════════════════════════════════════════════════════════════════════════

TIER4_REGULATORY_FEEDS: list[Source] = [
    # ── Global ──────────────────────────────────────────────────────────
    Source(
        name="IMO News",
        url="https://www.imo.org/en/MediaCentre/Pages/WhatsNew.aspx",
        source_key="imo",
        source_type="official",
        tier=4,
        modes=["ocean"],
        reliability=0.95,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    Source(
        name="WCO News",
        url="https://www.wcoomd.org/en/media/newsroom.aspx",
        source_key="wco",
        source_type="official",
        tier=4,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.95,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    Source(
        name="IATA Cargo Updates",
        url="https://www.iata.org/en/programs/cargo/",
        source_key="iata_cargo",
        source_type="official",
        tier=4,
        modes=["air"],
        reliability=0.95,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    Source(
        name="ICAO — Safety & Security",
        url="https://www.icao.int/Newsroom/Pages/default.aspx",
        source_key="icao",
        source_type="official",
        tier=4,
        modes=["air"],
        reliability=0.95,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    # ── US ──────────────────────────────────────────────────────────────
    Source(
        name="US CBP Trade Updates",
        url="https://www.cbp.gov/newsroom/rss-feeds",
        source_key="us_cbp",
        source_type="official",
        tier=4,
        modes=["ocean", "air", "road", "multimodal"],
        reliability=0.95,
        ingestion_method="rss",
    ),
    Source(
        name="US Federal Register — Trade",
        url="https://www.federalregister.gov/documents/search.atom?conditions[agencies][]=customs-and-border-protection&conditions[type][]=RULE&per_page=20",
        source_key="us_fed_register",
        source_type="official",
        tier=4,
        modes=["ocean", "air", "multimodal"],
        reliability=0.95,
        ingestion_method="rss",
    ),
    Source(
        name="US FMC — Federal Maritime Commission",
        url="https://www.fmc.gov/feed/",
        source_key="us_fmc",
        source_type="official",
        tier=4,
        modes=["ocean"],
        reliability=0.95,
        ingestion_method="rss",
    ),
    Source(
        name="FMCSA — Motor Carrier Safety",
        url="https://www.fmcsa.dot.gov/newsroom/rss.xml",
        source_key="us_fmcsa",
        source_type="official",
        tier=4,
        modes=["road"],
        reliability=0.95,
        ingestion_method="rss",
    ),
    Source(
        name="STB — Surface Transportation Board",
        url="https://www.stb.gov/news-communications/latest-news/feed/",
        source_key="us_stb",
        source_type="official",
        tier=4,
        modes=["rail"],
        reliability=0.95,
        ingestion_method="rss",
    ),
    # ── EU ──────────────────────────────────────────────────────────────
    Source(
        name="EU DG TAXUD News",
        url="https://taxation-customs.ec.europa.eu/news_en",
        source_key="eu_dg_taxud",
        source_type="official",
        tier=4,
        modes=["ocean", "air", "rail", "road", "multimodal"],
        reliability=0.95,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    Source(
        name="ERA — EU Agency for Railways",
        url="https://www.era.europa.eu/content/press-releases_en",
        source_key="eu_era",
        source_type="official",
        tier=4,
        modes=["rail"],
        reliability=0.9,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    # ── UK ──────────────────────────────────────────────────────────────
    Source(
        name="UK HMRC Trade",
        url="https://www.gov.uk/government/organisations/hm-revenue-customs.atom",
        source_key="uk_hmrc",
        source_type="official",
        tier=4,
        modes=["ocean", "air", "multimodal"],
        reliability=0.9,
        ingestion_method="rss",
    ),
    # ── Turkey ──────────────────────────────────────────────────────────
    Source(
        name="Türkiye Ticaret Bakanlığı",
        url="https://www.ticaret.gov.tr/rss",
        source_key="tr_trade",
        source_type="official",
        tier=4,
        modes=["ocean", "road", "rail", "multimodal"],
        reliability=0.85,
        ingestion_method="rss",
    ),
    # ── Rail-specific ───────────────────────────────────────────────────
    Source(
        name="Union Pacific Service Alerts",
        url="https://www.up.com/customers/announcements/index.htm",
        source_key="up_rail",
        source_type="official",
        tier=4,
        modes=["rail"],
        reliability=0.9,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    Source(
        name="BNSF Service Alerts",
        url="https://www.bnsf.com/ship-with-bnsf/maps-and-shipping-locations/service-alerts.html",
        source_key="bnsf_rail",
        source_type="official",
        tier=4,
        modes=["rail"],
        reliability=0.9,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    Source(
        name="CSX Service Alerts",
        url="https://www.csx.com/index.cfm/library/files/about-us/news-feed/",
        source_key="csx_rail",
        source_type="official",
        tier=4,
        modes=["rail"],
        reliability=0.9,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
    Source(
        name="Norfolk Southern Service Updates",
        url="https://www.norfolksouthern.com/en/ship-with-us/service-updates",
        source_key="ns_rail",
        source_type="official",
        tier=4,
        modes=["rail"],
        reliability=0.9,
        needs_playwright=True,
        ingestion_method="playwright",
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
#  AGGREGATE HELPERS
# ═══════════════════════════════════════════════════════════════════════════

_ALL_TIER_LISTS = [
    TIER1_LIVE_FEEDS,
    TIER1_CYBER_FEEDS,
    TIER1_GEOINT_FEEDS,
    TIER2_NEWS_FEEDS,
    TIER2_CHOKEPOINT_FEEDS,
    TIER2_PRICING_FEEDS,
    TIER2_MACRO_FEEDS,
    TIER3_SOCIAL_SOURCES,
    TIER4_REGULATORY_FEEDS,
]


def get_tier1_sources() -> list[Source]:
    """All Tier 1 sources (15-min cycle)."""
    return TIER1_LIVE_FEEDS + TIER1_CYBER_FEEDS + TIER1_GEOINT_FEEDS


def get_tier1_rss_sources() -> list[Source]:
    """Tier 1 sources that use RSS (no Playwright, no API)."""
    return [
        s for s in get_tier1_sources()
        if s.ingestion_method == "rss"
    ]


def get_tier1_playwright_sources() -> list[Source]:
    """Tier 1 sources that need Playwright scraping."""
    return [s for s in get_tier1_sources() if s.needs_playwright]


def get_tier1_api_sources() -> list[Source]:
    """Tier 1 sources that use JSON/REST APIs."""
    return [
        s for s in get_tier1_sources()
        if s.ingestion_method == "api"
    ]


def get_all_rss_sources() -> list[Source]:
    """All RSS-parseable sources across all tiers.

    Excludes sources that need Playwright or custom JSON APIs.
    """
    return [
        s
        for tier_list in _ALL_TIER_LISTS
        for s in tier_list
        if s.ingestion_method == "rss"
    ]


def get_noaa_source() -> Source | None:
    """Return the NOAA source (uses JSON API, not RSS)."""
    for s in TIER2_CHOKEPOINT_FEEDS:
        if s.source_key == "noaa_alerts":
            return s
    return None


def get_tier2_playwright_sources() -> list[Source]:
    """Tier 2 sources that need Playwright scraping."""
    return [
        s
        for s in TIER2_NEWS_FEEDS + TIER2_CHOKEPOINT_FEEDS + TIER2_PRICING_FEEDS + TIER2_MACRO_FEEDS
        if s.needs_playwright
    ]


def get_tier4_rss_sources() -> list[Source]:
    """Tier 4 sources that have RSS/Atom feeds (no Playwright needed)."""
    return [s for s in TIER4_REGULATORY_FEEDS if not s.needs_playwright]


def get_tier4_scrape_sources() -> list[Source]:
    """Tier 4 sources that need Playwright scraping."""
    return [s for s in TIER4_REGULATORY_FEEDS if s.needs_playwright]


def get_social_sources() -> list[Source]:
    """All Tier 3 social intelligence sources."""
    return TIER3_SOCIAL_SOURCES


def get_api_sources() -> list[Source]:
    """All sources that use JSON/REST API ingestion (across all tiers)."""
    return [
        s
        for tier_list in _ALL_TIER_LISTS
        for s in tier_list
        if s.ingestion_method == "api"
    ]


def get_all_sources() -> list[Source]:
    """Every registered source across all tiers."""
    result: list[Source] = []
    for tier_list in _ALL_TIER_LISTS:
        result.extend(tier_list)
    return result


def get_allowed_domains() -> set[str]:
    """Build domain allowlist from all registered sources."""
    from urllib.parse import urlparse

    domains: set[str] = set()
    for source in get_all_sources():
        hostname = urlparse(source.url).hostname
        if hostname:
            domains.add(hostname)
    return domains


# Pre-computed allowlist for fast lookups at runtime
ALLOWED_DOMAINS: set[str] = get_allowed_domains()


# ═══════════════════════════════════════════════════════════════════════════
#  LEGACY KEY MAPPER — bridges old DB keys to new per-source keys
# ═══════════════════════════════════════════════════════════════════════════


class LegacySourceMapper:
    """Map legacy generic DB source_weight keys to current per-source keys.

    The original DB had generic keys like 'tier1_news', 'reddit', 'ais'.
    These were split into per-source keys. This mapper lets the scoring
    engine resolve legacy keys without breaking existing signals.
    """

    _LEGACY_MAP: dict[str, list[str]] = {
        "tier1_news": [
            "lloyds_list", "tradewinds", "gcaptain", "splash247",
            "maritime_executive", "hellenic_shipping", "seatrade",
        ],
        "reddit": [
            "reddit_logistics", "reddit_freight", "reddit_supplychain",
            "reddit_shipping", "reddit_truckers", "reddit_aviation",
            "reddit_freightbrokers",
        ],
        "general_news": [
            "reuters_supply_chain", "bloomberg_supply_chain",
            "freightwaves", "joc", "supplychaindive", "loadstar",
        ],
        "twitter": [],  # Deprecated — no replacement
        "linkedin": [],  # Deprecated — no active feed
        "ais": [
            "marinetraffic", "vesselfinder", "opensky", "flightradar24",
        ],
        "carrier_direct": [
            "project44", "fourkites",
        ],
        "freight_index": [
            "freightos_fbx", "freightos_fbx_live", "xeneta",
            "baltic_exchange", "tac_index", "dat_freight",
        ],
    }

    # Reverse map: new key → legacy key (for weight fallback)
    _REVERSE_MAP: dict[str, str] = {
        new: legacy
        for legacy, news in _LEGACY_MAP.items()
        for new in news
    }

    @classmethod
    def resolve(cls, source_key: str) -> list[str]:
        """If source_key is a legacy key, return its modern replacements.

        If it's already a modern key, return [source_key].
        """
        return cls._LEGACY_MAP.get(source_key, [source_key])

    @classmethod
    def is_legacy(cls, source_key: str) -> bool:
        """Check if a key is one of the deprecated legacy keys."""
        return source_key in cls._LEGACY_MAP

    @classmethod
    def legacy_parent(cls, source_key: str) -> str | None:
        """Return the legacy parent key for a modern key, or None."""
        return cls._REVERSE_MAP.get(source_key)

    @classmethod
    def get_weight_key(cls, source_key: str) -> str:
        """Return the best key to look up in source_weights.

        Prefers the exact key; falls back to legacy parent if the exact
        key might not exist in the DB yet.
        """
        return source_key
