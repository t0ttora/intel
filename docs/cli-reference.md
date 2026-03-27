# NobleCLI Reference

NobleCLI is a Rich-powered terminal tool for inspecting, querying, and managing Noble Intel.

## Installation

NobleCLI is included when you install the package:

```bash
pip install -e .
noblecli --help
```

## Modes

### Local Mode (default)
Connects directly to PostgreSQL and Qdrant on the same machine. Use this when running on the VPS.

```bash
noblecli status
noblecli query "Suez Canal disruption"
```

### Remote Mode
Connects to the Noble Intel API over HTTPS. Use this from your laptop.

```bash
export NOBLE_INTEL_URL=https://intel.yourdomain.com
export INTEL_API_KEY=your-api-key
noblecli status
noblecli query "Panama Canal drought"
```

Remote mode is auto-detected when `NOBLE_INTEL_URL` is set.

## Commands

### `noblecli query <text>`
Run an intelligence query through the full pipeline.

```bash
noblecli query "What is the risk at the Suez Canal?"
noblecli query "Red Sea shipping disruptions" --cascade --json
```

### `noblecli status`
System health overview: services, resources, signal flow, source health.

```bash
noblecli status
```

### `noblecli signals`
List recent signals with filters.

```bash
noblecli signals                          # Last 24h, all tiers
noblecli signals --tier CRITICAL          # Only critical
noblecli signals --zone suez_canal        # By geo zone
noblecli signals --min-risk 0.6           # Risk threshold
noblecli signals --hours 48 --limit 20   # Custom window
```

### `noblecli risk`
Risk scoring tools.

```bash
noblecli risk score "Port closure at Shanghai"       # Score arbitrary text
noblecli risk cascade suez_canal 0.85                # Simulate cascade
noblecli risk grc                                     # Current GRC
noblecli risk scenario disruption_assessment 0.80    # Run scenario
```

### `noblecli sources`
Source calibration inspector.

```bash
noblecli sources list          # All source weights
noblecli sources set reddit 0.45   # Manually adjust weight
```

### `noblecli qdrant`
Vector database inspector.

```bash
noblecli qdrant info           # Collection stats
noblecli qdrant search "port congestion"   # Semantic search
noblecli qdrant stats          # Detailed storage stats
```

### `noblecli services`
Systemd service management (VPS only).

```bash
noblecli services status                  # All services
noblecli services logs intel-api          # Tail logs
noblecli services restart intel-worker    # Restart a service
```

### `noblecli pipeline`
Manual pipeline triggers.

```bash
noblecli pipeline rss                     # Run RSS ingestion now
noblecli pipeline scrape                  # Run scraper now
noblecli pipeline full                    # Full pipeline
noblecli pipeline rss --dry-run           # Preview without storing
```

### `noblecli alerts`
Alert management.

```bash
noblecli alerts list           # Active alerts
noblecli alerts push           # Manual alert push
```

### `noblecli calibration`
Manual calibration triggers.

```bash
noblecli calibration sources   # Recalibrate source weights
noblecli calibration formula   # Recalibrate formula weights
noblecli calibration cascade   # Recalibrate cascade edges
noblecli calibration drift     # Check for weight drift
noblecli calibration all       # Run all calibrations
```

### `noblecli system`
System management.

```bash
noblecli system cleanup        # Remove old signals
noblecli system info           # System info
noblecli system config         # Show current config
noblecli system health         # Quick health check
```

### `noblecli dashboard`
Full-screen live TUI dashboard (Textual-based). Auto-refreshes every 5 seconds.

```bash
noblecli dashboard
```

Features:
- Real-time signal table
- Alert panel
- Status bar with service health
- Works in both local and remote mode
- Press `q` or `Ctrl+C` to exit

## Output Formats

Most commands support `--json` flag for machine-readable output:

```bash
noblecli status --json | jq '.services'
noblecli signals --json | jq '.[] | select(.risk_score > 0.8)'
```

Default output uses Rich formatting with colors, tables, and panels.
