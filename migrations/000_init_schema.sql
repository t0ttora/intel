-- Noble Intel v3.0 — Base schema
-- Extracted from setup-local.sh so migrations are self-contained.
--
-- Run: psql -U noble noble_intel -f migrations/000_init_schema.sql

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- ── Signals ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL,
    tier TEXT NOT NULL,
    geo_zone TEXT,
    title TEXT,
    content TEXT NOT NULL,
    url TEXT,
    risk_score REAL,
    anomaly_score REAL,
    source_weight REAL,
    geo_criticality REAL,
    time_decay REAL,
    embedding_id TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_signals_risk ON signals (risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_signals_tier ON signals (tier);
CREATE INDEX IF NOT EXISTS idx_signals_geo ON signals (geo_zone);
CREATE INDEX IF NOT EXISTS idx_signals_created ON signals (created_at DESC);

-- ── Source Weights ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS source_weights (
    source TEXT PRIMARY KEY,
    current_weight REAL NOT NULL,
    base_weight REAL NOT NULL,
    floor_weight REAL NOT NULL,
    ceiling_weight REAL NOT NULL,
    total_signals INTEGER DEFAULT 0,
    total_accurate INTEGER DEFAULT 0,
    last_calibrated_at TIMESTAMPTZ DEFAULT now()
);
INSERT INTO source_weights (source, current_weight, base_weight, floor_weight, ceiling_weight) VALUES
    ('imo', 0.95, 0.95, 0.85, 1.00),
    ('ukmto', 0.95, 0.95, 0.85, 1.00),
    ('carrier_direct', 0.85, 0.85, 0.70, 0.95),
    ('ais', 0.80, 0.80, 0.70, 0.95),
    ('freight_index', 0.80, 0.80, 0.70, 0.90),
    ('tier1_news', 0.70, 0.70, 0.50, 0.85),
    ('general_news', 0.65, 0.65, 0.45, 0.80),
    ('reddit', 0.40, 0.40, 0.15, 0.70),
    ('twitter', 0.35, 0.35, 0.10, 0.65),
    ('linkedin', 0.45, 0.45, 0.20, 0.70)
ON CONFLICT (source) DO NOTHING;

-- ── Alerts ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID REFERENCES signals(id),
    risk_level TEXT NOT NULL,
    risk_score REAL NOT NULL,
    cascade_data JSONB,
    pushed_to_supabase BOOLEAN DEFAULT false,
    pushed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ── Outcomes ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID REFERENCES signals(id),
    predicted_impact TEXT,
    actual_outcome TEXT,
    accuracy_score REAL,
    lead_time_hours REAL,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);
