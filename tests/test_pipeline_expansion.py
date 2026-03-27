"""Quick verification of the pipeline expansion."""
import sys

print("Testing imports...")
from app.ingestion.sources import Source, get_all_sources
print("  sources.py OK")
from app.ingestion.rss import fetch_all_feeds, fetch_regulatory_feeds, RawSignal
print("  rss.py OK")
from app.ingestion.scraper import scrape_all_social, scrape_all_regulatory, scrape_all_sources
print("  scraper.py OK")
from app.ingestion.pipeline import ingest_signals
print("  pipeline.py OK")
from app.ingestion.filters import passes_keyword_filter, LOGISTICS_KEYWORDS
print("  filters.py OK")

# Test expanded keyword filter
tests = [
    ("Air cargo congestion at FRA airport", True),
    ("Rail freight embargo on Union Pacific", True),
    ("Trucking drayage shortage in LA", True),
    ("IATA hazmat directive update", True),
    ("Best Italian restaurants in Milan", False),
]
print()
print("Keyword filter tests:")
failed = 0
for text, expected in tests:
    result = passes_keyword_filter(text)
    status = "PASS" if result == expected else "FAIL"
    if result != expected:
        failed += 1
    print(f"  {status}: '{text[:50]}' -> {result} (expected {expected})")

# Test signal tagger multimodal detection
from app.intelligence.signal_tagger import tag_signal
print()
print("Signal tagger tests:")
tests2 = [
    ("Container vessel delayed at Shanghai port", "ocean"),
    ("Air cargo capacity crunch at Dubai airport IATA", "air"),
    ("Rail freight embargo BNSF intermodal terminal", "rail"),
    ("Trucking chassis shortage drayage", "road"),
    ("Port congestion driving air cargo surge at airport", "multimodal"),
]
for text, expected_mode in tests2:
    mode, region = tag_signal(text)
    status = "PASS" if mode == expected_mode else "FAIL"
    if mode != expected_mode:
        failed += 1
    print(f"  {status}: '{text[:50]}' -> mode={mode} (expected {expected_mode})")

# Test social impact filter
from app.ingestion.scraper import passes_impact_filter
print()
print("Impact filter tests:")
impact_tests = [
    ("Major delay at LAX cargo terminal", True),
    ("Strike announced at Rotterdam port", True),
    ("Congestion causing 3-day backlog", True),
    ("Had a great day at work today", False),
    ("Rate hike announced by Maersk", True),
]
for text, expected in impact_tests:
    result = passes_impact_filter(text)
    status = "PASS" if result == expected else "FAIL"
    if result != expected:
        failed += 1
    print(f"  {status}: '{text[:50]}' -> {result} (expected {expected})")

print()
if failed:
    print(f"FAILED: {failed} tests")
    sys.exit(1)
else:
    print("ALL TESTS PASSED")
