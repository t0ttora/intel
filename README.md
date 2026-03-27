# Noble Intel v3.0

**Adaptive Logistics Decision Engine** — real-time maritime intelligence with RAG-powered signal ingestion, adaptive risk scoring, cascade propagation, and scenario simulation.

Built to run on a single Hetzner CX33 VPS (4 vCPU, 8 GB RAM). Ingests 10 RSS feeds + web sources every 5 minutes, scores signals with an adaptive 4-component risk model, and serves intelligence via REST API and a terminal dashboard.

---

## What It Does

1. **Ingests** maritime/logistics signals from RSS feeds, Reddit, and web scrapers
2. **Filters** noise (63% rejection rate) and detects prompt injection attacks
3. **Embeds** signals using Gemini `text-embedding-004` (768-dim, free tier)
4. **Scores** each signal: `RISK = anomaly×w_a + source×w_s + geo×w_g + time×w_t`
5. **Cascades** high-risk events through a geo-dependency graph (Suez → Rotterdam → Hamburg)
6. **Fuses** multiple events into a Global Risk Composite (GRC)
7. **Simulates** delay/cost scenarios with p10/p50/p90 distributions
8. **Alerts** on CRITICAL signals (risk ≥ 0.80) → pushes to Supabase
9. **Self-calibrates** — weights adapt weekly/monthly based on prediction accuracy

---

## Quick Start

### Deploy to VPS (one command)

```bash
ssh root@your-vps-ip
curl -O https://raw.githubusercontent.com/t0ttora/intel/main/setup-vps.sh
bash setup-vps.sh
```

The script installs everything: PostgreSQL, Qdrant, Redis, Python, Caddy, systemd services, backups. You just provide your Gemini API key and Supabase credentials.

See [docs/deployment.md](docs/deployment.md) for full details.

### Local Development

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

### Run the API (requires PostgreSQL, Qdrant, Redis)

```bash
cp .env.example .env   # fill in credentials
uvicorn app.main:app --port 8000
celery -A app.tasks.celery_app worker --concurrency=2
celery -A app.tasks.celery_app beat
```

---

## API

```bash
# Health check (no auth)
curl http://localhost:8000/health

# Intelligence query
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "Suez Canal blockage impact", "include_cascade": true}'

# List signals
curl http://localhost:8000/api/v1/signals?tier=CRITICAL&hours=24 \
  -H "X-API-Key: your-key"
```

| Method | Path | Auth | Rate Limit |
|--------|------|------|-----------|
| POST | `/api/v1/query` | API Key | 30/min |
| GET | `/api/v1/signals` | API Key | — |
| GET | `/health` | None | — |
| WS | `/cli/ws/dashboard` | None | — |

See [docs/api-reference.md](docs/api-reference.md) for full request/response schemas.

---

## CLI

```bash
# On the VPS (local mode — direct DB access)
noblecli status
noblecli query "Red Sea route disruptions"
noblecli signals --tier CRITICAL --limit 10
noblecli risk cascade suez_canal 0.85
noblecli dashboard                        # full-screen Textual TUI

# From your laptop (remote mode — via HTTPS)
export NOBLE_INTEL_URL=https://intel.yourdomain.com
export INTEL_API_KEY=your-key
noblecli status
noblecli query "Panama Canal drought update"
```

See [docs/cli-reference.md](docs/cli-reference.md) for all commands.

---

## Risk Scoring (NOBLE-RSM v2)

```
RISK_SCORE = anomaly × 0.4 + source × 0.2 + geo × 0.2 + time × 0.2
```

| Tier | Score | Action |
|------|-------|--------|
| CRITICAL | ≥ 0.80 | Alert pushed to Supabase |
| HIGH | ≥ 0.60 | Elevated monitoring |
| MEDIUM | ≥ 0.40 | Standard monitoring |
| LOW | < 0.40 | Informational |

Weights self-calibrate monthly via Pearson correlation against outcomes. Source weights recalibrate weekly. See [docs/risk-scoring.md](docs/risk-scoring.md).

---

## Celery Schedule

| Task | Frequency | Description |
|------|-----------|-------------|
| RSS Ingestion | Every 5 min | Fetch 10 maritime RSS feeds |
| Web Scraper | Every 30 min | Reddit + Playwright scraping |
| Alert Check | Every 1 min | Push risk ≥ 0.80 to Supabase |
| Source Calibration | Weekly | Recalibrate source weights |
| Formula Calibration | Monthly | Recalibrate risk formula |
| Cascade Calibration | Weekly | Recalibrate geo-dependency edges |
| Cleanup | Daily 02:00 | Remove signals older than 30 days |

---

## Architecture

```
RSS/Reddit/Web → Filter → Sanitize → Dedup → Chunk → Embed (Gemini 768-dim)
                                                         │
                                    ┌────────────────────┼────────────────────┐
                                    ▼                    ▼                    │
                              PostgreSQL 16          Qdrant 1.13             │
                              (structured)           (vectors)               │
                                    │                    │                    │
                                    └────────┬───────────┘                    │
                                             ▼                                │
                                     Scoring Engine (NOBLE-RSM v2)           │
                                             ▼                                │
                                     Intelligence Engine                     │
                                     ├─ Cascade BFS (depth 3)               │
                                     ├─ GRC Fusion                           │
                                     ├─ Pattern Detection (6 types)         │
                                     └─ Scenario Simulation                  │
                                             ▼                                │
                                     Query Pipeline (7 steps)                │
                                             ▼                                │
                                    ┌────────┴────────┐                      │
                                    ▼                 ▼                      │
                              FastAPI API       NobleCLI/TUI                │
                              (Caddy TLS)       (Typer+Rich)               │
                                                                             │
                              Celery + Redis ← Beat Scheduler ───────────────┘
```

See [docs/architecture.md](docs/architecture.md) for detailed system diagrams.

---

## Project Structure

```
├── setup-vps.sh              # One-command VPS deployment
├── pyproject.toml             # Dependencies + build config
├── .env.example               # Environment variable template
│
├── app/
│   ├── main.py                # FastAPI app with lifespan
│   ├── config.py              # pydantic-settings configuration
│   ├── dependencies.py        # FastAPI dependency injection
│   ├── db/                    # PostgreSQL: pool, models, queries
│   ├── vectordb/              # Qdrant: client, embedder, search
│   ├── ingestion/             # RSS, scraper, filters, dedup, sanitizer, chunker
│   ├── scoring/               # NOBLE-RSM v2: risk_scorer, anomaly, time_decay, geo
│   ├── engine/                # Cascade, GRC fusion, patterns, scenarios
│   ├── intelligence/          # Query pipeline, intent classifier, output builder
│   ├── calibration/           # Source weights, formula weights, cascade edges, drift
│   ├── alerts/                # Supabase alert pusher
│   ├── api/                   # REST router + Pydantic schemas
│   └── tasks/                 # Celery: ingest_rss, ingest_scraper, alert, calibrate, cleanup
│
├── cli/
│   ├── main.py                # Typer entry point (10 sub-commands)
│   ├── commands/              # status, signals, risk, sources, qdrant, services, pipeline, alerts, calibration, system
│   ├── server/                # CLI API router + WebSocket handler
│   ├── tui/                   # Textual live dashboard + widgets
│   └── remote/                # HTTP client for remote mode
│
├── tests/                     # 12 test files, ~85 tests
│   ├── test_risk_scorer.py
│   ├── test_cascade.py
│   ├── test_fusion.py
│   ├── test_filters.py
│   ├── test_dedup.py
│   ├── test_time_decay.py
│   ├── test_sanitizer.py
│   ├── test_chunker.py
│   ├── test_calibration.py
│   ├── test_scenarios.py
│   └── test_api.py
│
└── docs/
    ├── architecture.md        # System architecture + diagrams
    ├── api-reference.md       # Full API documentation
    ├── risk-scoring.md        # NOBLE-RSM v2 algorithm details
    ├── cli-reference.md       # All CLI commands
    ├── deployment.md          # VPS deployment guide
    └── environment-variables.md
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| API | FastAPI 0.115.6 |
| Task Queue | Celery 5.4.0 + Redis 7 |
| Vector DB | Qdrant 1.13.2 (self-hosted, free) |
| Database | PostgreSQL 16 |
| Embeddings | Gemini text-embedding-004 (free tier) |
| CLI | Typer 0.15.1 + Rich 13.9.4 + Textual 1.0.0 |
| Validation | Pydantic 2.10.4 |
| Scraping | Playwright 1.49.0 |
| Reverse Proxy | Caddy (auto-TLS) |
| Error Tracking | Sentry (optional) |
| Target OS | Ubuntu 24.04 LTS |
| Target Hardware | Hetzner CX33 (4 vCPU, 8 GB) |

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | System design, data flow, component overview |
| [API Reference](docs/api-reference.md) | Endpoints, request/response schemas, error codes |
| [Risk Scoring](docs/risk-scoring.md) | NOBLE-RSM v2 formula, calibration, cascade, GRC |
| [CLI Reference](docs/cli-reference.md) | All NobleCLI commands and usage |
| [Deployment](docs/deployment.md) | VPS setup, systemd, security, backups, troubleshooting |
| [Environment Variables](docs/environment-variables.md) | All config variables and how to obtain them |

---

## License

Proprietary — NobleVerse
