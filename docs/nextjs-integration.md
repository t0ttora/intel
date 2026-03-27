# NextJS Integration

How the NobleVerse AI assistant connects to the Intel API to answer logistics intelligence queries.

## Data Flow

```
User asks: "What are the risks at Suez Canal?"
  │
  ▼
NobleVerse Chat UI → AI Module (Gemini 2.5 Flash)
  │
  ▼
Gemini decides to call tool: query_logistics_intel
  │
  ▼
Tool handler: POST https://intel.nobleverse.com/api/v1/query
  Headers: X-API-Key: <NOBLE_INTEL_KEY>
  Body: { "query": "risks at Suez Canal", "include_cascade": true }
  │
  ▼
Intel API runs 7-step pipeline:
  1. Intent classification
  2. Geo zone detection
  3. Signal retrieval (hybrid: PostgreSQL + Qdrant vectors)
  4. Cascade propagation (BFS over geo-dependency graph)
  5. GRC fusion (Global Risk Composite)
  6. Scenario simulation (p10/p50/p90)
  7. Output builder (structured JSON)
  │
  ▼
Structured JSON response → back to Gemini
  │
  ▼
Gemini reasons over the data → natural language response to user
```

## Environment Variables

Add to your NobleVerse `.env`:

```env
# Intel API connection
NOBLE_INTEL_URL=https://intel.nobleverse.com
NOBLE_INTEL_KEY=<INTEL_API_KEY from VPS setup>
```

## Tool Handler

Create `src/modules/ai/tools/handlers/query-logistics-intel.ts`:

```typescript
import type { ToolHandler } from '../types'

const INTEL_API_URL = process.env.NOBLE_INTEL_URL
const INTEL_API_KEY = process.env.NOBLE_INTEL_KEY

export const queryLogisticsIntel: ToolHandler = async (args) => {
  if (!INTEL_API_URL || !INTEL_API_KEY) {
    return { error: 'Intel service not configured' }
  }

  try {
    const response = await fetch(`${INTEL_API_URL}/api/v1/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': INTEL_API_KEY,
      },
      body: JSON.stringify({
        query: args.query,
        geo_zone: args.geo_zone ?? null,
        min_risk_score: args.min_risk_score ?? null,
        include_cascade: args.include_cascade ?? true,
        include_user_impact: args.include_user_impact ?? false,
        user_id: args.user_id ?? null,
      }),
      signal: AbortSignal.timeout(15_000),
    })

    if (!response.ok) {
      return { error: `Intel API returned ${response.status}` }
    }

    return await response.json()
  } catch (err) {
    // Fallback: if Intel API is down, return error for Gemini to handle gracefully
    return { error: 'Intel service unavailable — try web_search as fallback' }
  }
}
```

## Tool Registration

Register in the AI tool registry:

```typescript
{
  name: 'query_logistics_intel',
  description:
    'Query the Noble Intel logistics intelligence engine for real-time risk assessments, ' +
    'chokepoint status, cascade propagation analysis, and supply chain disruption scenarios. ' +
    'Use this tool when the user asks about shipping risks, port congestion, trade lane disruptions, ' +
    'regulatory changes, or any logistics intelligence question.',
  parameters: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'Intelligence query text (3-500 chars)',
      },
      geo_zone: {
        type: 'string',
        description:
          'Specific geo zone code: suez_canal, strait_of_malacca, panama_canal, ' +
          'bab_el_mandeb, hormuz, shanghai, singapore, rotterdam, etc. Auto-detected if omitted.',
      },
      min_risk_score: {
        type: 'number',
        description: 'Minimum risk score filter (0.0 to 1.0)',
      },
      include_cascade: {
        type: 'boolean',
        description: 'Include cascade propagation analysis (default: true)',
      },
      include_user_impact: {
        type: 'boolean',
        description: 'Include impact on user active shipments (default: false)',
      },
      user_id: {
        type: 'string',
        description: 'User ID for personalized shipment impact (required if include_user_impact is true)',
      },
    },
    required: ['query'],
  },
  handler: queryLogisticsIntel,
}
```

## Response Schema

The Intel API returns this structure (Gemini uses it to compose its answer):

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
    "avg_source_weight": 0.72,
    "freshest_signal_age_hours": 0.3,
    "degraded_sources": [],
    "fallback_mode": null
  },
  "generated_at": "2026-03-27T12:00:00Z",
  "ttl_hours": 1,
  "scenario": {
    "reroute_probability": 0.78,
    "delay_distribution": { "p10": 3, "p50": 7, "p90": 14, "unit": "days" },
    "cost_distribution": { "p10": 1200, "p50": 3500, "p90": 8000, "unit": "USD/TEU" }
  },
  "cascade": {
    "propagation_depth": 2,
    "affected_zones": ["bab_el_mandeb", "hormuz", "singapore"],
    "downstream_effects": "Congestion cascade from Suez → Red Sea → Strait of Malacca"
  },
  "signals": [
    {
      "id": "uuid",
      "source": "tier1_news",
      "tier": "CRITICAL",
      "title": "Suez Canal blockage enters day 3",
      "risk_score": 0.91,
      "created_at": "2026-03-27T10:00:00Z"
    }
  ],
  "sources": [
    { "type": "tier1_news", "weight": 0.70, "url": "https://..." }
  ]
}
```

## Fallback Strategy

If the Intel API is unavailable (5xx, timeout, network error):

1. The tool handler returns `{ error: "Intel service unavailable" }`
2. Gemini sees the error and falls back to `web_search` (Tavily) for real-time logistics data
3. The user still gets an answer, but without the structured risk scoring and cascade analysis

## Alert Integration (P0 Alerts)

Intel automatically pushes CRITICAL alerts (risk >= 0.80) to the Supabase `logistics_alerts` table. The NobleVerse `context-builder.ts` picks these up and injects them into the AI conversation automatically, so Gemini is aware of critical events even before the user asks.

```
Intel Celery → alert_check every 1 min → risk >= 0.80?
  → Yes → INSERT INTO logistics_alerts (Supabase)
  → context-builder.ts reads active alerts
  → Gemini system prompt includes: "ACTIVE ALERT: Suez Canal blockage, risk 0.91"
```

## Rate Limits

| Endpoint | Limit | Scope | Enforcement |
|----------|-------|-------|-------------|
| `POST /api/v1/query` | 30 req/min | Per API key | In-memory counter |
| `GET /api/v1/signals` | 60 req/min | Per API key | In-memory counter |

If rate-limited, the API returns `429 Too Many Requests`. The tool handler should let Gemini know so it can inform the user to wait.
