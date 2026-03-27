# API Reference

Noble Intel exposes a FastAPI REST API on port 8000 (behind Caddy reverse proxy with TLS in production).

## Authentication

All endpoints except `/health` require an API key via the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-key" https://your-domain.com/api/v1/signals
```

## Endpoints

### GET `/health`

Health check. No authentication required.

**Response:**
```json
{
  "status": "ok",
  "version": "3.0.0",
  "timestamp": "2026-03-27T12:00:00Z"
}
```

---

### POST `/api/v1/query`

Execute an intelligence query through the full 7-step pipeline.

**Rate limit:** 30 requests/minute per API key.

**Request body:**
```json
{
  "query": "What is the risk at the Suez Canal?",
  "geo_zone": "suez_canal",         // optional — auto-detected if omitted
  "min_risk_score": 0.4,             // optional — filter minimum
  "include_cascade": true,           // optional — default true
  "include_user_impact": false,      // optional — default false
  "user_id": null                    // optional — for personalized impact
}
```

**Response:**
```json
{
  "risk_level": "CRITICAL",
  "risk_score": 0.85,
  "global_risk_composite": 0.9231,
  "event_summary": "[REUTERS] Suez Canal blockage | [FREIGHTWAVES] Delays mounting",
  "confidence": 0.82,
  "data_quality": {
    "level": 0,
    "level_name": "FULL",
    "signal_count": 15,
    "source_diversity": 4,
    "avg_source_weight": 0.680,
    "freshest_signal_age_hours": 0.5,
    "degraded_sources": [],
    "fallback_mode": null
  },
  "scenario": {
    "intent": "disruption_assessment",
    "reroute_probability": 0.75,
    "delay_distribution": {
      "p10": 3,
      "p50": 7,
      "p90": 14,
      "unit": "days"
    },
    "cost_distribution": {
      "p10": 500,
      "p50": 1200,
      "p90": 3000,
      "unit": "USD/TEU"
    }
  },
  "cascade": {
    "source_zone": "suez_canal",
    "source_risk": 0.85,
    "propagation_depth": 2,
    "affected_zones": [
      "rotterdam_congestion",
      "freight_spike_asia_eu",
      "cape_reroute"
    ],
    "nodes": [
      {"zone": "rotterdam_congestion", "propagated_risk": 0.72, "hop": 1},
      {"zone": "freight_spike_asia_eu", "propagated_risk": 0.68, "hop": 1},
      {"zone": "cape_reroute", "propagated_risk": 0.60, "hop": 1}
    ],
    "downstream_effects": "rotterdam_congestion (risk: 0.72, hop 1); ..."
  },
  "user_impact": null,
  "sources": [
    {
      "type": "tier1_news",
      "weight": 0.700,
      "url": "https://gcaptain.com/...",
      "title": "Suez Canal vessel grounding causes delays"
    }
  ],
  "ttl_hours": 1,
  "generated_at": "2026-03-27T12:00:00Z"
}
```

**Data Quality Levels:**

| Level | Name | Description |
|-------|------|-------------|
| 0 | FULL | All systems operational, high confidence |
| 1 | PARTIAL | Some sources degraded, acceptable confidence |
| 2 | HISTORICAL | Stale data (>6h), using historical signals |
| 3 | RAG_OFFLINE | Vector search unavailable, DB-only fallback |
| 4 | FULL_DEGRADATION | Minimal data available, low confidence |

**TTL by risk level:**
- CRITICAL: 1 hour
- HIGH: 3 hours
- MEDIUM: 6 hours
- LOW: 12 hours

---

### GET `/api/v1/signals`

List stored signals with filters.

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tier` | string | — | Filter by tier (CRITICAL, HIGH, MEDIUM, LOW) |
| `geo_zone` | string | — | Filter by geo zone |
| `source` | string | — | Filter by source type |
| `min_risk` | float | — | Minimum risk score |
| `hours` | int | 24 | Lookback window in hours |
| `limit` | int | 50 | Max results (max 200) |
| `offset` | int | 0 | Pagination offset |

**Response:**
```json
{
  "signals": [
    {
      "id": "uuid",
      "source": "tier1_news",
      "tier": "CRITICAL",
      "geo_zone": "suez_canal",
      "title": "Vessel grounding blocks Suez Canal",
      "content": "...",
      "url": "https://...",
      "risk_score": 0.85,
      "anomaly_score": 0.72,
      "source_weight": 0.70,
      "geo_criticality": 0.95,
      "time_decay": 0.98,
      "created_at": "2026-03-27T10:30:00Z"
    }
  ],
  "total": 284,
  "limit": 50,
  "offset": 0
}
```

---

### WebSocket `/cli/ws/dashboard`

Live dashboard feed for the NobleCLI TUI. Sends JSON payloads every 5 seconds.

**Message format:**
```json
{
  "status": { "services": {...}, "resources": {...} },
  "signals": { "recent": [...], "counts": {...} },
  "risk": { "grc": 0.62, "active_events": [...] }
}
```

## Error Responses

All errors return standard JSON:

```json
{
  "detail": "Error description"
}
```

| Status | Meaning |
|--------|---------|
| 401 | Missing or invalid API key |
| 422 | Request validation error (Pydantic) |
| 429 | Rate limit exceeded (30 req/min on /query) |
| 500 | Internal server error (details logged to Sentry, generic message returned) |

## CLI Endpoints (`/cli/*`)

These are internal endpoints used by NobleCLI in remote mode:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/cli/status` | System status JSON |
| GET | `/cli/signals` | Signal listing |
| GET | `/cli/sources` | Source weights |
| WS | `/cli/ws/dashboard` | Live dashboard stream |
