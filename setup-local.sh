#!/usr/bin/env bash
# ============================================================================
# Noble Intel v3.0 — Local macOS Setup Script
# Requires: Homebrew, Python 3.12, Docker Desktop
# Run from inside the intel/ directory:
#   bash setup-local.sh
# ============================================================================
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
step() { echo -e "\n${BLUE}${BOLD}── $1 ──${NC}\n"; }

# ── Pre-flight ───────────────────────────────────────────────────────────────
step "Pre-flight checks"

if ! command -v brew &>/dev/null; then
    echo "Homebrew not found. Install from https://brew.sh then re-run." && exit 1
fi
if ! command -v docker &>/dev/null; then
    echo "Docker not found. Install Docker Desktop from https://www.docker.com/products/docker-desktop/ then re-run." && exit 1
fi
if ! docker info &>/dev/null; then
    echo "Docker daemon not running. Open Docker Desktop first." && exit 1
fi
log "Homebrew and Docker are ready"

# ── PostgreSQL ───────────────────────────────────────────────────────────────
step "PostgreSQL 16"

if ! brew list postgresql@16 &>/dev/null; then
    brew install postgresql@16
fi
brew services start postgresql@16 2>/dev/null || true
sleep 2

# Create user + database if they don't exist
/opt/homebrew/opt/postgresql@16/bin/psql postgres -tc "SELECT 1 FROM pg_roles WHERE rolname='noble'" \
    | grep -q 1 || /opt/homebrew/opt/postgresql@16/bin/createuser -s noble 2>/dev/null || true

/opt/homebrew/opt/postgresql@16/bin/psql -U noble postgres -tc "SELECT 1 FROM pg_database WHERE datname='noble_intel'" \
    | grep -q 1 || /opt/homebrew/opt/postgresql@16/bin/createdb -U noble noble_intel 2>/dev/null || true

# Create schema
/opt/homebrew/opt/postgresql@16/bin/psql -U noble noble_intel << 'SCHEMA'
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

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
    ('imo', 0.95, 0.95, 0.85, 1.00), ('ukmto', 0.95, 0.95, 0.85, 1.00),
    ('carrier_direct', 0.85, 0.85, 0.70, 0.95), ('ais', 0.80, 0.80, 0.70, 0.95),
    ('freight_index', 0.80, 0.80, 0.70, 0.90), ('tier1_news', 0.70, 0.70, 0.50, 0.85),
    ('general_news', 0.65, 0.65, 0.45, 0.80), ('reddit', 0.40, 0.40, 0.15, 0.70),
    ('twitter', 0.35, 0.35, 0.10, 0.65), ('linkedin', 0.45, 0.45, 0.20, 0.70)
ON CONFLICT (source) DO NOTHING;

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
SCHEMA

log "PostgreSQL ready — noble_intel database created"
log "DATABASE_URL=postgresql://noble@127.0.0.1:5432/noble_intel"

# ── Qdrant ───────────────────────────────────────────────────────────────────
step "Qdrant 1.13.2 (Docker)"

# Skip if Qdrant is already responding on port 6333
if curl -sf http://127.0.0.1:6333/healthz > /dev/null 2>&1; then
    warn "Qdrant already running on :6333 — skipping container start"
else
    docker rm -f qdrant-local 2>/dev/null || true
    # Stop any other qdrant containers that may own the port
    docker stop $(docker ps -q --filter "ancestor=qdrant/qdrant") 2>/dev/null || true
    docker run -d \
        --name qdrant-local \
        --restart unless-stopped \
        -p 127.0.0.1:6333:6333 \
        qdrant/qdrant:v1.13.2

    echo -n "Waiting for Qdrant..."
    for i in {1..20}; do
        if curl -sf http://127.0.0.1:6333/healthz > /dev/null 2>&1; then
            echo " ready"; break
        fi
        echo -n "."; sleep 1
    done
fi

# Create collection if it doesn't exist (idempotent — ignore 4xx if already exists)
curl -sf -X PUT http://127.0.0.1:6333/collections/intel_signals \
    -H 'Content-Type: application/json' \
    -d '{"vectors":{"size":768,"distance":"Cosine"},"on_disk_payload":true}' > /dev/null 2>&1 || true

log "Qdrant ready — http://127.0.0.1:6333"
log "QDRANT_URL=http://127.0.0.1:6333  (no API key needed locally)"

# ── Redis ────────────────────────────────────────────────────────────────────
step "Redis 7"

if ! brew list redis &>/dev/null; then
    brew install redis
fi
brew services start redis 2>/dev/null || true
sleep 1
log "Redis ready — no password in local mode"
log "REDIS_URL=redis://127.0.0.1:6379/0"

# ── Python venv ───────────────────────────────────────────────────────────────
step "Python 3.12 virtualenv"

if ! command -v python3.12 &>/dev/null; then
    brew install python@3.12
fi

if [[ ! -d ".venv" ]]; then
    python3.12 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -e ".[dev]" --quiet
log "Virtualenv ready at .venv/"

# ── .env ──────────────────────────────────────────────────────────────────────
step ".env configuration"

if [[ -f ".env" ]]; then
    warn ".env already exists — skipping. Edit it manually if needed."
else
    # Prompt only for the secrets you can't auto-configure
    read -rp "Gemini API key (required for embeddings): " GEMINI_KEY
    read -rp "Supabase URL (optional, press Enter to skip): " SB_URL
    read -rp "Supabase service key (optional, press Enter to skip): " SB_KEY

    INTEL_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")

    cat > .env << ENVFILE
# Noble Intel — Local Development
GEMINI_API_KEY=${GEMINI_KEY}

# PostgreSQL (no password — local Homebrew install)
DATABASE_URL=postgresql://noble@127.0.0.1:5432/noble_intel

# Qdrant (no API key in local mode)
QDRANT_URL=http://127.0.0.1:6333
QDRANT_API_KEY=
QDRANT_COLLECTION=intel_signals

# Redis (no password in local mode)
REDIS_PASSWORD=
REDIS_URL=redis://127.0.0.1:6379/0

# Supabase (optional — only needed for alert push)
SUPABASE_URL=${SB_URL}
SUPABASE_SERVICE_KEY=${SB_KEY}

# Intel API
INTEL_API_KEY=${INTEL_KEY}
INTEL_API_PORT=8000

# Sentry (optional)
SENTRY_DSN=
ENVFILE
    chmod 600 .env
    log ".env created"
fi

# ── Done ───────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}══════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  Noble Intel — Local Setup Complete${NC}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════${NC}"
echo ""
echo -e "${BOLD}Start the API:${NC}"
echo "  source .venv/bin/activate"
echo "  uvicorn app.main:app --port 8000 --reload"
echo ""
echo -e "${BOLD}Start Celery (new terminal):${NC}"
echo "  source .venv/bin/activate"
echo "  celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2"
echo ""
echo -e "${BOLD}Run tests:${NC}"
echo "  pytest tests/ -v"
echo ""
echo -e "${BOLD}CLI:${NC}"
echo "  noblecli status"
echo "  noblecli query \"Suez Canal disruption\""
echo ""
echo -e "${BOLD}Services running:${NC}"
echo "  PostgreSQL  → localhost:5432"
echo "  Qdrant      → http://127.0.0.1:6333"
echo "  Redis       → localhost:6379"
echo ""
echo -e "${YELLOW}To stop services:${NC}"
echo "  brew services stop postgresql@16 redis"
echo "  docker stop qdrant-local"
