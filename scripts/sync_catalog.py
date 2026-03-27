#!/usr/bin/env python3
"""Noble Intel — Source Registry Synchronization Engine.

Three-phase reconciliation between:
  1. docs/source-catalog.md   (348 entries — planning doc)
  2. app/ingestion/sources.py (106 entries — runtime code)
  3. source_weights DB table  (47 entries — scoring weights)

Usage:
    # Phase 1: Backfill catalog with sources.py entries it's missing
    python scripts/sync_catalog.py backfill

    # Phase 2: Generate Source() definitions for catalog entries not in code
    python scripts/sync_catalog.py generate [--verified-only] [--dry-run]

    # Phase 3: Reconcile DB source_weights with sources.py
    python scripts/sync_catalog.py db-sync [--dry-run]

    # All phases
    python scripts/sync_catalog.py all [--dry-run]
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "docs" / "source-catalog.md"
SOURCES_PY_PATH = ROOT / "app" / "ingestion" / "sources.py"

# ═══════════════════════════════════════════════════════════════════════════
#  Shared Data Structures
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class CatalogEntry:
    """A single row parsed from a catalog markdown table."""

    name: str
    primary_mode: str
    data_type: str
    geo_scope: str
    source_key: str
    source_type: str
    tier: int
    reliability: float
    ingestion_method: str
    needs_playwright: bool
    url: str
    status: str  # [V], [U], [P]
    section: str = ""  # Which ## section it belongs to


@dataclass
class CodeSource:
    """A source_key extracted from sources.py with its metadata."""

    source_key: str
    name: str
    url: str
    source_type: str
    tier: int
    modes: list[str] = field(default_factory=lambda: ["ocean"])
    reliability: float = 0.5
    ingestion_method: str = "rss"
    needs_playwright: bool = False


# ═══════════════════════════════════════════════════════════════════════════
#  Parsers
# ═══════════════════════════════════════════════════════════════════════════


def parse_catalog() -> list[CatalogEntry]:
    """Parse all table rows from source-catalog.md into CatalogEntry objects."""
    text = CATALOG_PATH.read_text(encoding="utf-8")
    entries: list[CatalogEntry] = []
    current_section = ""

    for line in text.splitlines():
        # Track section headers
        if line.startswith("## ") and not line.startswith("## Table"):
            current_section = line.strip("# ").strip()
            continue

        # Skip non-table rows, headers, and separator lines
        if not line.startswith("|") or "source_key" in line or "---" in line:
            continue

        cells = [c.strip() for c in line.split("|")]
        # Strip empty leading/trailing cells from | delimited lines
        cells = [c for c in cells if c != ""][:12]

        if len(cells) < 12:
            continue

        try:
            tier = int(cells[6]) if cells[6].isdigit() else 2
            reliability = float(cells[7]) if cells[7].replace(".", "").isdigit() else 0.5
        except (ValueError, IndexError):
            continue

        entry = CatalogEntry(
            name=cells[0],
            primary_mode=cells[1].lower(),
            data_type=cells[2],
            geo_scope=cells[3],
            source_key=cells[4],
            source_type=cells[5],
            tier=tier,
            reliability=reliability,
            ingestion_method=cells[8],
            needs_playwright=cells[9].lower() == "true",
            url=cells[10],
            status=cells[11] if len(cells) > 11 else "[U]",
            section=current_section,
        )
        entries.append(entry)

    return entries


def parse_sources_py() -> list[CodeSource]:
    """Extract all Source() definitions from sources.py via regex."""
    text = SOURCES_PY_PATH.read_text(encoding="utf-8")
    sources: list[CodeSource] = []

    # Match each Source(...) block
    pattern = re.compile(
        r'Source\(\s*'
        r'name="([^"]*)",\s*'
        r'url="([^"]*)",\s*'
        r'source_key="([^"]*)",\s*'
        r'source_type="([^"]*)",\s*'
        r'tier=(\d+),',
        re.DOTALL,
    )

    for match in pattern.finditer(text):
        name, url, source_key, source_type, tier = match.groups()

        # Extract optional fields from the same Source() block
        # Find the closing ) for this Source block
        start = match.start()
        depth = 0
        end = start
        for i in range(start, len(text)):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        block = text[start:end]

        # Parse modes
        modes_match = re.search(r'modes=\[([^\]]*)\]', block)
        modes = ["ocean"]
        if modes_match:
            modes = [m.strip().strip('"').strip("'") for m in modes_match.group(1).split(",")]

        # Parse reliability
        rel_match = re.search(r'reliability=([\d.]+)', block)
        reliability = float(rel_match.group(1)) if rel_match else 0.5

        # Parse ingestion_method
        ing_match = re.search(r'ingestion_method="([^"]*)"', block)
        ingestion_method = ing_match.group(1) if ing_match else "rss"

        # Parse needs_playwright
        pw_match = re.search(r'needs_playwright=True', block)
        needs_playwright = bool(pw_match)

        sources.append(CodeSource(
            source_key=source_key,
            name=name,
            url=url,
            source_type=source_type,
            tier=int(tier),
            modes=modes,
            reliability=reliability,
            ingestion_method=ingestion_method,
            needs_playwright=needs_playwright,
        ))

    return sources


def get_code_source_keys() -> set[str]:
    """Fast extraction of just the source_key values from sources.py."""
    text = SOURCES_PY_PATH.read_text(encoding="utf-8")
    return set(re.findall(r'source_key="([^"]*)"', text))


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 1 — Backfill Catalog
# ═══════════════════════════════════════════════════════════════════════════


def phase1_backfill() -> int:
    """Append sources.py entries missing from catalog into a new section."""
    catalog_entries = parse_catalog()
    catalog_keys = {e.source_key for e in catalog_entries}
    code_sources = parse_sources_py()

    missing = [s for s in code_sources if s.source_key not in catalog_keys]

    if not missing:
        print("Phase 1: Catalog is complete — no missing entries.")
        return 0

    print(f"Phase 1: {len(missing)} sources in code not in catalog. Backfilling...")

    # Build the markdown section
    lines: list[str] = [
        "",
        "---",
        "",
        "## [AUTOMATED_BACKFILL] — Sources in Code Not in Catalog",
        "",
        f"> **Auto-generated**: {len(missing)} sources from `sources.py` that were missing from this catalog.",
        "> Review and move entries to their proper sections above.",
        "",
        "| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type "
        "| tier | reliability | ingestion_method | needs_playwright | URL | Status |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    MODE_MAP = {
        "ocean": "Ocean",
        "air": "Air",
        "rail": "Rail",
        "road": "Road",
        "multimodal": "Multimodal",
    }

    for s in sorted(missing, key=lambda x: (x.tier, x.source_key)):
        primary_mode = MODE_MAP.get(s.modes[0], "Multimodal") if s.modes else "Multimodal"
        if len(s.modes) > 1:
            primary_mode = "Multimodal"
        data_type = {
            "rss": "RSS",
            "api": "API",
            "playwright": "News Page",
            "bs4": "News Page",
        }.get(s.ingestion_method, "RSS")
        pw = "true" if s.needs_playwright else "false"

        lines.append(
            f"| {s.name} | {primary_mode} | {data_type} | Global "
            f"| {s.source_key} | {s.source_type} | {s.tier} "
            f"| {s.reliability:.2f} | {s.ingestion_method} | {pw} "
            f"| {s.url} | [CODE] |"
        )

    catalog_text = CATALOG_PATH.read_text(encoding="utf-8")

    # Remove old backfill section if present
    old_section = re.search(
        r'\n---\n\n## \[AUTOMATED_BACKFILL\].*',
        catalog_text,
        re.DOTALL,
    )
    if old_section:
        catalog_text = catalog_text[:old_section.start()]

    # Find insertion point: before "## Source Count Summary" or at end
    insert_match = re.search(r'\n## Source Count Summary', catalog_text)
    if insert_match:
        catalog_text = (
            catalog_text[:insert_match.start()]
            + "\n".join(lines)
            + "\n"
            + catalog_text[insert_match.start():]
        )
    else:
        catalog_text += "\n".join(lines) + "\n"

    CATALOG_PATH.write_text(catalog_text, encoding="utf-8")
    print(f"  Appended {len(missing)} entries to [AUTOMATED_BACKFILL] section.")
    return len(missing)


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 2 — Generate Source() Definitions
# ═══════════════════════════════════════════════════════════════════════════


def _mode_string(primary_mode: str) -> str:
    """Convert catalog mode to sources.py modes list string."""
    mode_map: dict[str, list[str]] = {
        "ocean": ["ocean"],
        "air": ["air"],
        "rail": ["rail"],
        "road": ["road"],
        "multimodal": ["ocean", "air", "rail", "road", "multimodal"],
        "air/road": ["air", "road"],
    }
    modes = mode_map.get(primary_mode.lower(), ["ocean"])
    return "[" + ", ".join(f'"{m}"' for m in modes) + "]"


def _tier_list_name(tier: int, source_type: str) -> str:
    """Determine which tier list this source should go into."""
    if source_type == "social":
        return "TIER3_SOCIAL_SOURCES"
    if tier == 1:
        if source_type in ("physical", "geoint"):
            return "TIER1_GEOINT_FEEDS"
        if source_type == "cyber":
            return "TIER1_CYBER_FEEDS"
        if source_type == "pricing":
            return "TIER1_LIVE_FEEDS"
        return "TIER1_LIVE_FEEDS"
    if tier == 2:
        if source_type == "pricing":
            return "TIER2_PRICING_FEEDS"
        if source_type in ("official",) and "chokepoint" in source_type:
            return "TIER2_CHOKEPOINT_FEEDS"
        return "TIER2_NEWS_FEEDS"
    if tier == 4:
        return "TIER4_REGULATORY_FEEDS"
    return "TIER2_NEWS_FEEDS"


def phase2_generate(verified_only: bool = False, dry_run: bool = False) -> int:
    """Generate Source() code for catalog entries missing from sources.py.

    Returns count of generated entries. If dry_run, prints but doesn't write.
    """
    catalog_entries = parse_catalog()
    code_keys = get_code_source_keys()

    missing = [
        e for e in catalog_entries
        if e.source_key not in code_keys
        and e.url.startswith("http")
        and e.status != "[P]"  # Skip paywalled
    ]

    if verified_only:
        missing = [e for e in missing if e.status == "[V]"]

    if not missing:
        print("Phase 2: All eligible catalog entries already in code.")
        return 0

    print(f"Phase 2: Generating {len(missing)} Source() definitions...")

    # Group by target tier list
    by_list: dict[str, list[CatalogEntry]] = {}
    for e in sorted(missing, key=lambda x: (x.tier, x.source_key)):
        target = _tier_list_name(e.tier, e.source_type)
        by_list.setdefault(target, []).append(e)

    output_path = ROOT / "scripts" / "generated_sources.py"
    lines: list[str] = [
        '"""Auto-generated Source() definitions from source-catalog.md.',
        "",
        "These entries exist in the catalog but not in sources.py.",
        "Review, then merge into the appropriate tier list in app/ingestion/sources.py.",
        "",
        f"Generated: {len(missing)} entries (excluding paywalled [P] sources).",
        '"""',
        "from app.ingestion.sources import Source",
        "",
    ]

    for list_name, entries in by_list.items():
        lines.append(f"# ── Target: {list_name} ({len(entries)} sources) " + "─" * 40)
        lines.append(f"{list_name}_NEW: list[Source] = [")

        for e in entries:
            modes = _mode_string(e.primary_mode)
            pw = "True" if e.needs_playwright else "False"
            kw = "True" if e.source_type == "social" else "False"
            api_env = ""
            if e.ingestion_method == "api":
                env_key = e.source_key.upper() + "_API_KEY"
                api_env = f'\n        api_key_env="{env_key}",'

            lines.append(f"    Source(")
            lines.append(f'        name="{e.name}",')
            lines.append(f'        url="{e.url}",')
            lines.append(f'        source_key="{e.source_key}",')
            lines.append(f'        source_type="{e.source_type}",')
            lines.append(f"        tier={e.tier},")
            lines.append(f"        modes={modes},")
            lines.append(f"        reliability={e.reliability},")
            if e.needs_playwright:
                lines.append(f"        needs_playwright={pw},")
            if e.source_type == "social":
                lines.append(f"        requires_keyword_filter={kw},")
            if api_env:
                lines.append(f"        {api_env.strip()}")
            lines.append(f'        ingestion_method="{e.ingestion_method}",')
            lines.append(f"    ),")

        lines.append("]")
        lines.append("")

    # Summary
    lines.append("")
    lines.append("# ── Summary ──────────────────────────────────────────")
    lines.append(f"# Total new sources: {len(missing)}")
    for list_name, entries in by_list.items():
        lines.append(f"#   {list_name}: +{len(entries)}")

    output_text = "\n".join(lines) + "\n"

    if dry_run:
        print(output_text)
        print(f"\n  [DRY RUN] Would write {len(missing)} entries to {output_path}")
    else:
        output_path.write_text(output_text, encoding="utf-8")
        print(f"  Wrote {len(missing)} entries to {output_path.relative_to(ROOT)}")

    return len(missing)


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE 3 — DB & Weight Reconciliation
# ═══════════════════════════════════════════════════════════════════════════

# Legacy DB keys that predate per-source splitting
LEGACY_KEY_MAP: dict[str, list[str]] = {
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
    "linkedin": ["linkedin_logistics"],
    "ais": ["marinetraffic", "vesselfinder", "opensky", "flightradar24"],
    "carrier_direct": ["project44", "fourkites"],
    "freight_index": [
        "freightos_fbx", "freightos_fbx_live", "xeneta",
        "baltic_exchange", "tac_index", "dat_freight",
    ],
}


def phase3_generate_sql(dry_run: bool = False) -> int:
    """Generate SQL to upsert source_weights for all sources in code.

    Returns count of upsert statements generated.
    """
    code_sources = parse_sources_py()
    catalog_entries = parse_catalog()

    # Build a combined weight lookup: code reliability takes precedence,
    # then catalog reliability, then 0.5 default
    catalog_weights = {e.source_key: e.reliability for e in catalog_entries}

    upsert_rows: list[tuple[str, float]] = []
    seen: set[str] = set()

    for s in code_sources:
        if s.source_key in seen:
            continue
        seen.add(s.source_key)
        weight = s.reliability
        # Compute floor/ceiling from weight
        floor_w = round(max(0.10, weight - 0.15), 2)
        ceiling_w = round(min(1.00, weight + 0.10), 2)
        upsert_rows.append((s.source_key, weight, weight, floor_w, ceiling_w))

    # Add catalog entries not in code (but with valid URLs, not paywalled)
    for e in catalog_entries:
        if e.source_key in seen or e.status == "[P]":
            continue
        if not e.url.startswith("http"):
            continue
        seen.add(e.source_key)
        weight = e.reliability
        floor_w = round(max(0.10, weight - 0.15), 2)
        ceiling_w = round(min(1.00, weight + 0.10), 2)
        upsert_rows.append((e.source_key, weight, weight, floor_w, ceiling_w))

    sql_path = ROOT / "migrations" / "002_sync_source_weights.sql"
    lines: list[str] = [
        "-- Noble Intel — Auto-generated source_weights sync",
        f"-- Total: {len(upsert_rows)} source weight entries",
        "-- Upserts all sources from sources.py + catalog (excluding paywalled)",
        "--",
        "-- Run: psql -U noble noble_intel -f migrations/002_sync_source_weights.sql",
        "",
        "INSERT INTO source_weights (source, current_weight, base_weight, floor_weight, ceiling_weight) VALUES",
    ]

    for i, (key, cw, bw, fw, ceil_w) in enumerate(sorted(upsert_rows)):
        comma = "," if i < len(upsert_rows) - 1 else ""
        lines.append(f"    ('{key}', {cw:.2f}, {bw:.2f}, {fw:.2f}, {ceil_w:.2f}){comma}")

    lines.append("ON CONFLICT (source) DO UPDATE SET")
    lines.append("    base_weight = EXCLUDED.base_weight,")
    lines.append("    floor_weight = EXCLUDED.floor_weight,")
    lines.append("    ceiling_weight = EXCLUDED.ceiling_weight;")
    lines.append("")
    lines.append("-- Verify")
    lines.append("SELECT count(*) AS total_source_weights FROM source_weights;")
    lines.append("")

    sql_text = "\n".join(lines)

    if dry_run:
        print(sql_text)
        print(f"\n  [DRY RUN] Would write {len(upsert_rows)} upserts to {sql_path}")
    else:
        sql_path.write_text(sql_text, encoding="utf-8")
        print(f"  Wrote {len(upsert_rows)} upserts to {sql_path.relative_to(ROOT)}")

    return len(upsert_rows)


# ═══════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    verified_only = "--verified-only" in sys.argv

    if cmd == "backfill":
        n = phase1_backfill()
        print(f"\nPhase 1 complete: {n} entries backfilled into catalog.")

    elif cmd == "generate":
        n = phase2_generate(verified_only=verified_only, dry_run=dry_run)
        print(f"\nPhase 2 complete: {n} Source() definitions generated.")

    elif cmd == "db-sync":
        n = phase3_generate_sql(dry_run=dry_run)
        print(f"\nPhase 3 complete: {n} source_weights upserts generated.")

    elif cmd == "all":
        print("=" * 60)
        n1 = phase1_backfill()
        print()
        n2 = phase2_generate(verified_only=verified_only, dry_run=dry_run)
        print()
        n3 = phase3_generate_sql(dry_run=dry_run)
        print()
        print("=" * 60)
        print(f"SUMMARY: backfilled {n1}, generated {n2}, db-synced {n3}")

    elif cmd == "stats":
        catalog = parse_catalog()
        code_keys = get_code_source_keys()
        catalog_keys = {e.source_key for e in catalog}

        print(f"Catalog entries:     {len(catalog)}")
        print(f"Code source_keys:    {len(code_keys)}")
        print(f"Overlap:             {len(catalog_keys & code_keys)}")
        print(f"Catalog-only:        {len(catalog_keys - code_keys)}")
        print(f"Code-only:           {len(code_keys - catalog_keys)}")
        print(f"Verified [V]:        {sum(1 for e in catalog if e.status == '[V]')}")
        print(f"Paywalled [P]:       {sum(1 for e in catalog if e.status == '[P]')}")
        print(f"Unverified [U]:      {sum(1 for e in catalog if e.status == '[U]')}")

    else:
        print(f"Unknown command: {cmd}")
        print("Commands: backfill | generate | db-sync | all | stats")
        sys.exit(1)


if __name__ == "__main__":
    main()
