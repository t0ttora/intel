# Risk Scoring — NOBLE-RSM v2

The Noble Risk Scoring Model (NOBLE-RSM) v2 is an adaptive 4-component formula for scoring logistics intelligence signals.

## Formula

```
RISK_SCORE = anomaly × w_a + source × w_s + geo × w_g + time × w_t
```

Where:
- **anomaly** — anomaly score (0.0–1.0)
- **source** — source credibility weight (0.0–1.0)
- **geo** — geographic criticality (0.0–1.0)
- **time** — time decay factor (0.0–1.0)

Default weights: `w_a=0.40, w_s=0.20, w_g=0.20, w_t=0.20` (sum = 1.0)

## Components

### Anomaly Score
Two sub-components combined:

1. **Sigmoid z-score**: measures how unusual a signal's numeric value is relative to the running mean
   ```
   z = (value - mean) / stddev
   anomaly = 1 / (1 + e^(-z))
   ```

2. **Keyword density**: log-scaled count of logistics-specific keywords in the text
   ```
   density = log(1 + keyword_count) / log(1 + max_expected)
   ```

### Source Weight
Each signal source has a credibility weight that adapts over time:

| Source | Base Weight | Floor | Ceiling |
|--------|-----------|-------|---------|
| IMO | 0.95 | 0.85 | 1.00 |
| UKMTO | 0.95 | 0.85 | 1.00 |
| Carrier Direct | 0.85 | 0.70 | 0.95 |
| AIS | 0.80 | 0.70 | 0.95 |
| Freight Index | 0.80 | 0.70 | 0.90 |
| Tier 1 News | 0.70 | 0.50 | 0.85 |
| General News | 0.65 | 0.45 | 0.80 |
| LinkedIn | 0.45 | 0.20 | 0.70 |
| Reddit | 0.40 | 0.15 | 0.70 |
| Twitter | 0.35 | 0.10 | 0.65 |

Weights are recalibrated weekly based on prediction accuracy (learning rate 0.05).

### Geo Criticality
Static criticality scores for 17 logistics zones:

| Zone | Criticality |
|------|------------|
| Suez Canal | 0.95 |
| Strait of Malacca | 0.90 |
| Bab el-Mandeb | 0.92 |
| Panama Canal | 0.88 |
| Strait of Hormuz | 0.90 |
| Taiwan Strait | 0.85 |
| Shanghai | 0.80 |
| Singapore | 0.82 |
| Rotterdam | 0.78 |
| ... | ... |

Auto-detected from signal content via keyword matching.

### Time Decay
Exponential decay with 12-hour half-life:

```
decay = 0.5 ^ (hours_since_signal / 12)
```

A signal that is:
- 0h old → decay = 1.00
- 6h old → decay = 0.71
- 12h old → decay = 0.50
- 24h old → decay = 0.25
- 48h old → decay = 0.06

## Risk Tiers

| Tier | Score Range | Action |
|------|------------|--------|
| CRITICAL | ≥ 0.80 | Immediate alert pushed to Supabase |
| HIGH | ≥ 0.60 | Elevated monitoring |
| MEDIUM | ≥ 0.40 | Standard monitoring |
| LOW | < 0.40 | Informational only |

## Adaptive Calibration

### Source Weight Calibration (Weekly)
For each source, compares predicted risk against actual outcomes:
```
accuracy = accurate_predictions / total_predictions
new_weight = old_weight + lr × (accuracy - 0.5)
```
Learning rate: 0.05. Weights are clamped to floor/ceiling bounds.

### Formula Weight Calibration (Monthly)
Computes Pearson correlation between each component and actual outcomes:
```
r_anomaly = pearson(anomaly_scores, outcome_scores)
r_source  = pearson(source_weights, outcome_scores)
...
```
Weights are rebalanced proportional to correlation, with a minimum of 0.10 per weight.

### Cascade Edge Calibration (Weekly)
Adjusts edge weights in the geo-dependency graph based on observed downstream impacts:
```
new_edge = old_edge + lr × (observed_impact - expected_impact)
```
Learning rate: 0.03.

### Drift Detection
Flags sources whose current weight has drifted > 0.20 from their base weight.

## Cascade Propagation

When a high-risk event hits a zone, risk cascades through the geo-dependency graph:

```
suez_canal ──0.9──▶ rotterdam_congestion
           ──0.8──▶ freight_spike_asia_eu
           ──0.7──▶ cape_reroute ──0.6──▶ cape_congestion
           ──0.6──▶ singapore_overload
```

**BFS parameters:**
- Max depth: 3 hops
- Decay per hop: 0.85×
- Minimum propagated risk: 0.30 (pruned below this)

**Example:** Suez Canal (risk 0.85):
- Hop 1: rotterdam_congestion = 0.85 × 0.9 × 0.85 = 0.65
- Hop 2: hamburg_overflow = 0.65 × 0.6 × 0.85 = 0.33
- Hop 3: anything below 0.30 is pruned

## GRC (Global Risk Composite)

Fuses multiple independent risk events into a single score:

```
GRC = 1 - Π(1 - Rᵢ)
```

Where Rᵢ is the risk score of event i.

**Example:** Two events at risk 0.70 and 0.50:
```
GRC = 1 - (1-0.70) × (1-0.50) = 1 - 0.30 × 0.50 = 0.85
```

## Scenario Simulation

For each query intent, generates probabilistic delay/cost distributions:

| Intent | Base Delay (p50) | Base Cost (p50) |
|--------|-----------------|-----------------|
| disruption_assessment | 7 days | 1200 USD/TEU |
| route_risk | 5 days | 800 USD/TEU |
| cost_forecast | 3 days | 600 USD/TEU |
| timeline_impact | 10 days | 1500 USD/TEU |
| general_risk | 5 days | 800 USD/TEU |

Distributions are risk-scaled: p10 = base × 0.5 × risk, p50 = base × risk, p90 = base × 2.0 × risk.
