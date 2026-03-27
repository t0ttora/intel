# Architecture

Noble Intel is a single-node logistics intelligence engine deployed on a Hetzner CX33 VPS (4 vCPU, 8 GB RAM). It ingests signals from maritime/logistics RSS feeds and web sources, scores them with an adaptive risk model, and serves intelligence via a REST API.

## System Diagram

```
                         ┌──────────────────────────────────┐
                         │           DATA SOURCES            │
                         │                                   │
                         │  10 RSS Feeds (Lloyd's, IMO, ...)│
                         │  3 Reddit Subreddits              │
                         │  Web Scrapers (Playwright)         │
                         └──────────┬───────────────────────┘
                                    │
                          ┌─────────▼─────────┐
                          │  INGESTION LAYER   │
                          │                    │
                          │  Keyword Filter    │  63% rejection rate
                          │  Prompt Sanitizer  │  Blocks injection attacks
                          │  Content Dedup     │  SHA-256 + cosine ≥0.92
                          │  Text Chunker      │  300-500 token chunks
                          └────────┬───────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼                              ▼
             ┌──────────┐                  ┌──────────────┐
             │PostgreSQL │                  │   Qdrant     │
             │  16       │                  │  1.13.2      │
             │           │                  │              │
             │ signals   │                  │ 768-dim      │
             │ weights   │                  │ Cosine       │
             │ alerts    │                  │ on_disk      │
             │ outcomes  │                  │              │
             └─────┬─────┘                  └──────┬───────┘
                   │                               │
                   └──────────┬────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  SCORING ENGINE    │
                    │                    │
                    │  NOBLE-RSM v2      │
                    │  Adaptive weights  │
                    │  4-component       │
                    └────────┬───────────┘
                             │
                    ┌────────▼──────────┐
                    │ INTELLIGENCE       │
                    │ ENGINE             │
                    │                    │
                    │ Cascade BFS        │  Max depth 3, 0.85 decay
                    │ GRC Fusion         │  1 - Π(1-Rᵢ)
                    │ Pattern Detection  │  6 pattern types
                    │ Scenario Sim       │  p10/p50/p90 distributions
                    └────────┬──────────┘
                             │
                    ┌────────▼──────────┐
                    │  QUERY PIPELINE    │
                    │  (7 steps)         │
                    │                    │
                    │  1. Intent classify│
                    │  2. Geo detection  │
                    │  3. Signal retrival│
                    │  4. Cascade prop.  │
                    │  5. GRC fusion     │
                    │  6. Scenario sim   │
                    │  7. Output build   │
                    └───────┬────────────┘
                            │
              ┌─────────────┼────────────────┐
              ▼                              ▼
       ┌──────────┐                  ┌──────────────┐
       │ REST API │                  │  NobleCLI    │
       │ FastAPI  │                  │ Typer + Rich │
       │          │                  │ + Textual    │
       │ /query   │                  │              │
       │ /signals │                  │ Local mode   │
       │ /health  │                  │ Remote mode  │
       └──────────┘                  └──────────────┘
```

## Component Overview

### Ingestion Layer (`app/ingestion/`)
- **RSS Fetcher** — 10 maritime/logistics feeds, polled every 5 minutes via Celery
- **Web Scraper** — Reddit JSON API + Playwright browser scraping, every 30 minutes
- **Keyword Filter** — regex-based logistics keyword gate, rejects ~63% of noise
- **Sanitizer** — detects and blocks prompt injection patterns in signal content
- **Dedup** — SHA-256 content hashing + Qdrant cosine similarity (threshold 0.92)
- **Chunker** — sentence-boundary splitting into 300-500 token chunks with 200-char overlap

### Storage
- **PostgreSQL 16** — signals, source_weights, alerts, outcomes tables
- **Qdrant 1.13.2** — vector search, 768-dim Gemini embeddings, cosine similarity, on-disk payloads

### Scoring Engine (`app/scoring/`)
- **NOBLE-RSM v2** — `RISK = anomaly×w_a + source×w_s + geo×w_g + time×w_t`
- **Anomaly detector** — sigmoid z-score + log-scaled keyword density
- **Time decay** — half-life 12 hours, exponential decay
- **Geo criticality** — 17 predefined logistics zones with static criticality scores

### Intelligence Engine (`app/engine/`)
- **Cascade propagation** — BFS over geo-dependency graph (8 source zones), max depth 3, 0.85 decay per hop
- **GRC fusion** — Global Risk Composite: `GRC = 1 - Π(1 - Rᵢ)` over active events
- **Pattern detection** — vessel clusters, dwell anomalies, reroutes, blank sailings, dark fleet, congestion spikes
- **Scenario simulation** — intent-based p10/p50/p90 distributions for delays and costs

### Calibration System (`app/calibration/`)
- **Source weights** — weekly recalibration against prediction accuracy (lr=0.05)
- **Formula weights** — monthly Pearson correlation against outcomes, rebalanced with min 0.10
- **Cascade edges** — weekly edge weight adjustment (lr=0.03)
- **Drift detection** — flags sources with weight delta > 0.20

### Alert System (`app/alerts/`)
- Checks for signals with risk ≥ 0.80 every minute
- Pushes CRITICAL alerts to Supabase `logistics_alerts` table

## Data Flow

```
Signal source → Keyword filter → Sanitizer → Deduplicator
  → Embed (Gemini text-embedding-004, 768-dim)
  → Store: PostgreSQL (structured) + Qdrant (vectors)
  → Score: anomaly + source + geo + time → RISK_SCORE
  → Classify: CRITICAL/HIGH/MEDIUM/LOW
  → If CRITICAL: push alert to Supabase
```

## Embedding Model

Google Gemini `text-embedding-004`:
- **Dimensions**: 768
- **Free tier**: 1,500 req/min, 216,000/day
- Batched (max 100 texts per call)
- Zero-vector fallback on API failure

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| API Framework | FastAPI | 0.115.6 |
| Task Queue | Celery + Redis | 5.4.0 |
| Vector DB | Qdrant | 1.13.2 |
| Database | PostgreSQL | 16 |
| Embeddings | Gemini text-embedding-004 | — |
| CLI | Typer + Rich + Textual | 0.15.1 / 13.9.4 / 1.0.0 |
| HTTP Client | httpx | 0.28.1 |
| Validation | Pydantic | 2.10.4 |
| Browser Scraping | Playwright | 1.49.0 |
| Error Tracking | Sentry | 2.19.2 |
| Reverse Proxy | Caddy | latest |
| OS | Ubuntu 24.04 LTS | — |
