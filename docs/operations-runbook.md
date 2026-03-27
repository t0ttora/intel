# Operations Runbook

Day-to-day operations, monitoring, and incident response for Noble Intel running on VPS.

## What Runs 24/7

### Systemd Services

| Service | Process | Memory Limit | Restart Policy |
|---------|---------|-------------|----------------|
| `intel-api` | uvicorn (2 workers) | 512 MB | Always, 5s delay |
| `intel-worker` | Celery worker (concurrency 2) | 1.5 GB | Always, 10s delay |
| `intel-scheduler` | Celery beat | 256 MB | Always, 10s delay |

### Background Tasks (Celery Beat Schedule)

| Task | Schedule | Purpose |
|------|----------|---------|
| `tier1-live-every-15m` | Every 15 min | Live physical data, pricing APIs, GEOINT, cyber |
| `tier2-rss-every-1h` | Every 1 hour | News RSS, chokepoint status, Playwright scrapers |
| `tier3-social-every-5m` | Every 5 min | Reddit, forums (impact-filtered) |
| `tier4-regulatory-daily` | Daily 06:00 UTC | Customs, embargoes, sanctions |
| `event-pipeline-every-15m` | Every 15 min | Event fusion pipeline (aligned with Tier 1) |
| `check-alerts-every-1m` | Every 1 min | Push CRITICAL alerts (risk >= 0.80) to Supabase |
| `calibrate-sources-weekly` | Monday 03:00 UTC | Source weight recalibration |
| `calibrate-formula-monthly` | 1st of month 04:00 UTC | Formula weight rebalancing |
| `calibrate-cascade-weekly` | Sunday 03:00 UTC | Cascade edge adjustment |
| `cleanup-expired-daily` | Daily 02:00 UTC | Expire old signals, prune vectors |

### Cron Jobs

| Job | Schedule | Purpose |
|-----|----------|---------|
| `backup.sh` | Daily 03:00 UTC | Encrypted PostgreSQL dump (7-day retention) |
| `unattended-upgrades` | Auto | Ubuntu security patches |

## Monitoring Commands

### Quick Status Check

```bash
# All services at a glance
sudo systemctl status intel-api intel-worker intel-scheduler

# Or use NobleCLI
source /opt/noble-intel/.venv/bin/activate
noblecli status
```

### Health Endpoint

```bash
# Local
curl http://127.0.0.1:8000/health

# Public
curl https://intel.nobleverse.com/health
```

Response:
```json
{
  "status": "ok",
  "version": "3.0.0",
  "uptime_seconds": 86400,
  "commit": "abc1234"
}
```

### Logs

```bash
# API logs (live)
sudo journalctl -u intel-api -f

# Worker logs
tail -f /data/logs/celery-worker.log

# Beat/scheduler logs
tail -f /data/logs/celery-beat.log

# Caddy access logs
tail -f /data/logs/caddy-access.log

# Backup logs
cat /data/logs/backup.log
```

### Database

```bash
# Connect to PostgreSQL
sudo -u noble psql -d noble_intel

# Signal count
sudo -u noble psql -d noble_intel -c "SELECT count(*) FROM signals;"

# Signals by tier
sudo -u noble psql -d noble_intel -c "SELECT tier, count(*) FROM signals GROUP BY tier ORDER BY count DESC;"

# Recent signals
sudo -u noble psql -d noble_intel -c "SELECT source, tier, risk_score, created_at FROM signals ORDER BY created_at DESC LIMIT 10;"

# Source weights
sudo -u noble psql -d noble_intel -c "SELECT * FROM source_weights ORDER BY current_weight DESC;"
```

### Qdrant

```bash
# Collection info
curl -s http://127.0.0.1:6333/collections/intel_signals \
  -H "api-key: $(grep QDRANT_API_KEY /opt/noble-intel/.env | cut -d= -f2)" \
  | python3 -m json.tool

# Vector count
curl -s http://127.0.0.1:6333/collections/intel_signals \
  -H "api-key: $(grep QDRANT_API_KEY /opt/noble-intel/.env | cut -d= -f2)" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Vectors: {d[\"result\"][\"points_count\"]}')"
```

### Redis

```bash
REDIS_PW=$(grep REDIS_PASSWORD /opt/noble-intel/.env | cut -d= -f2)

# Ping
redis-cli -a "$REDIS_PW" --no-auth-warning ping

# Queue length
redis-cli -a "$REDIS_PW" --no-auth-warning llen celery

# Memory usage
redis-cli -a "$REDIS_PW" --no-auth-warning info memory | grep used_memory_human
```

## Common Operations

### Restart All Services

```bash
sudo systemctl restart intel-api intel-worker intel-scheduler
```

### Restart a Single Service

```bash
sudo systemctl restart intel-api
```

### Force Re-ingest (Manual)

```bash
cd /opt/noble-intel
source .venv/bin/activate

# Trigger a specific tier manually
python -c "from app.tasks.ingest_rss import ingest_rss_task; ingest_rss_task()"
```

### Backup & Restore

```bash
# Manual backup
sudo -u noble /opt/noble-intel/backup.sh

# List backups
ls -la /data/cold/backups/

# Restore from backup
PASSPHRASE=$(sudo cat /etc/noble-backup-passphrase)
gpg --batch --decrypt --passphrase "$PASSPHRASE" \
  /data/cold/backups/pg_20260327.sql.gz.gpg \
  | gunzip | sudo -u postgres psql noble_intel
```

### Qdrant Snapshot

```bash
QDRANT_KEY=$(grep QDRANT_API_KEY /opt/noble-intel/.env | cut -d= -f2)

# Create snapshot
curl -X POST http://127.0.0.1:6333/collections/intel_signals/snapshots \
  -H "api-key: $QDRANT_KEY"

# List snapshots
curl http://127.0.0.1:6333/collections/intel_signals/snapshots \
  -H "api-key: $QDRANT_KEY"
```

## Incident Response

### Service Down (API not responding)

```bash
# 1. Check which service is down
sudo systemctl status intel-api intel-worker intel-scheduler

# 2. Check logs
sudo journalctl -u intel-api --no-pager -n 50

# 3. Common fixes:
# .env permissions
ls -la /opt/noble-intel/.env  # must be -rw------- noble noble
sudo chmod 600 /opt/noble-intel/.env
sudo chown noble:noble /opt/noble-intel/.env

# Port conflict
sudo lsof -i :8000

# Restart
sudo systemctl restart intel-api
```

### Disk Full

```bash
# Check disk
df -h

# Clean old backups
find /data/cold/backups -name "pg_*.sql.gz.gpg" -mtime +3 -delete

# Clean Docker
docker system prune -f

# Clean old logs
sudo truncate -s 0 /data/logs/celery-worker.log
```

### PostgreSQL Issues

```bash
# Check status
sudo systemctl status postgresql

# Check connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# Kill stuck queries
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in transaction' AND query_start < now() - interval '5 minutes';"
```

### Qdrant Down

```bash
docker ps | grep qdrant
docker logs qdrant --tail 30
docker restart qdrant
```

### High Memory

```bash
# Check per-process memory
ps aux --sort=-%mem | head -20

# Restart worker (clears child processes)
sudo systemctl restart intel-worker

# If Qdrant is eating RAM, check collection config
curl http://127.0.0.1:6333/collections/intel_signals \
  -H "api-key: $QDRANT_KEY" | python3 -m json.tool
```

## Resource Budget (Hetzner CX33: 4 vCPU, 8 GB RAM)

| Component | RAM Budget | CPU Budget |
|-----------|-----------|------------|
| PostgreSQL 16 | ~400 MB | Shared |
| Qdrant 1.13.2 | ~400 MB | Shared |
| Redis 7 | 256 MB (hard limit) | Minimal |
| Intel API (2 uvicorn workers) | ~512 MB | 100% CPU quota |
| Celery worker (2 concurrent) | ~1 GB | Shared |
| Celery beat | ~128 MB | Minimal |
| System + Caddy | ~500 MB | Minimal |
| **Total** | **~3.2 GB** | |
| **Headroom** | **~4.8 GB free** | |

## Log Rotation

Configured via `/etc/logrotate.d/noble-intel`:
- All files in `/data/logs/*.log`
- Daily rotation, 7-day retention
- Compressed with gzip after 1 day
- Empty files skipped
