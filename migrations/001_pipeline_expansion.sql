-- Noble Intel v3.1 — Pipeline expansion migration
-- Adds source_type, reliability_score columns and new source weights
-- for the multimodal ingestion pipeline.
--
-- Run: psql -U noble noble_intel -f migrations/001_pipeline_expansion.sql

-- ── New columns on signals table ────────────────────────────────────────
ALTER TABLE signals ADD COLUMN IF NOT EXISTS source_type TEXT;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS reliability_score REAL;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS content_hash TEXT;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS transport_mode TEXT;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS region TEXT;

-- ── Indexes for new filtering dimensions ────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_signals_source_type ON signals (source_type);
CREATE INDEX IF NOT EXISTS idx_signals_transport_mode ON signals (transport_mode);
CREATE INDEX IF NOT EXISTS idx_signals_region ON signals (region);
CREATE INDEX IF NOT EXISTS idx_signals_content_hash ON signals (content_hash);

-- ── New source weights for expanded data sources ────────────────────────
INSERT INTO source_weights (source, current_weight, base_weight, floor_weight, ceiling_weight) VALUES
    -- Ocean news (existing tier1_news split into per-source keys)
    ('lloyds_list', 0.90, 0.90, 0.80, 1.00),
    ('tradewinds', 0.85, 0.85, 0.75, 0.95),
    ('gcaptain', 0.80, 0.80, 0.65, 0.90),
    ('splash247', 0.75, 0.75, 0.60, 0.85),
    ('maritime_executive', 0.75, 0.75, 0.60, 0.85),
    ('hellenic_shipping', 0.70, 0.70, 0.55, 0.85),
    ('seatrade', 0.75, 0.75, 0.60, 0.85),
    -- Air cargo (NEW)
    ('aircargo_news', 0.85, 0.85, 0.70, 0.95),
    ('aircargo_world', 0.80, 0.80, 0.65, 0.90),
    ('flightglobal', 0.80, 0.80, 0.65, 0.90),
    ('cargo_facts', 0.80, 0.80, 0.65, 0.90),
    ('loadstar', 0.85, 0.85, 0.70, 0.95),
    -- Rail / Multimodal (NEW)
    ('railway_age', 0.75, 0.75, 0.60, 0.85),
    ('freightwaves', 0.80, 0.80, 0.65, 0.90),
    ('joc', 0.90, 0.90, 0.80, 1.00),
    ('supplychaindive', 0.75, 0.75, 0.60, 0.85),
    -- Road (NEW)
    ('transport_topics', 0.80, 0.80, 0.65, 0.90),
    ('overdrive', 0.70, 0.70, 0.55, 0.85),
    -- Chokepoints & Weather
    ('noaa_alerts', 0.95, 0.95, 0.85, 1.00),
    ('gdacs', 0.95, 0.95, 0.85, 1.00),
    -- Pricing
    ('freightos_fbx', 0.85, 0.85, 0.70, 0.95),
    ('xeneta', 0.85, 0.85, 0.70, 0.95),
    -- Social (per-subreddit keys instead of generic "reddit")
    ('reddit_logistics', 0.40, 0.40, 0.15, 0.70),
    ('reddit_freight', 0.40, 0.40, 0.15, 0.70),
    ('reddit_supplychain', 0.35, 0.35, 0.15, 0.65),
    ('reddit_shipping', 0.35, 0.35, 0.15, 0.65),
    ('reddit_truckers', 0.30, 0.30, 0.10, 0.60),
    ('reddit_aviation', 0.25, 0.25, 0.10, 0.55),
    -- Regulatory (NEW)
    ('wco', 0.95, 0.95, 0.85, 1.00),
    ('iata_cargo', 0.95, 0.95, 0.85, 1.00),
    ('us_cbp', 0.95, 0.95, 0.85, 1.00),
    ('us_fed_register', 0.95, 0.95, 0.85, 1.00),
    ('eu_dg_taxud', 0.95, 0.95, 0.85, 1.00),
    ('uk_hmrc', 0.90, 0.90, 0.80, 0.95),
    ('tr_trade', 0.85, 0.85, 0.70, 0.95),
    ('up_rail', 0.90, 0.90, 0.80, 0.95),
    ('bnsf_rail', 0.90, 0.90, 0.80, 0.95)
ON CONFLICT (source) DO NOTHING;

-- ── Verify ──────────────────────────────────────────────────────────────
SELECT count(*) AS total_source_weights FROM source_weights;
