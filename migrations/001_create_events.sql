-- Decision Engine v1.0 — Events + Event-Signal junction tables
-- Run against the noble_intel database.

CREATE TABLE IF NOT EXISTS events (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title         TEXT NOT NULL,
    summary       TEXT NOT NULL,
    impact_score  REAL NOT NULL DEFAULT 0,
    priority      TEXT NOT NULL DEFAULT 'LOW',
    transport_modes TEXT[] NOT NULL DEFAULT '{}',
    regions       TEXT[] NOT NULL DEFAULT '{}',
    confidence    REAL NOT NULL DEFAULT 0.5,
    signal_count  INTEGER NOT NULL DEFAULT 0,
    source_diversity INTEGER NOT NULL DEFAULT 0,
    decisions     JSONB NOT NULL DEFAULT '[]',
    cascade_effects JSONB NOT NULL DEFAULT '[]',
    status        TEXT NOT NULL DEFAULT 'active',
    start_time    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at    TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS event_signals (
    event_id  UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    signal_id UUID NOT NULL REFERENCES signals(id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, signal_id)
);

-- Query patterns: active events by priority, recent events, signal lookup
CREATE INDEX IF NOT EXISTS idx_events_priority ON events (priority);
CREATE INDEX IF NOT EXISTS idx_events_status_updated ON events (status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_event_signals_signal ON event_signals (signal_id);
