# Deployment Guide

Complete guide for deploying Noble Intel v3.0 to a Hetzner CX33 VPS (or any Ubuntu 24.04 server).

## Prerequisites

Before deploying, you need:

1. **A VPS** running Ubuntu 24.04 LTS with root SSH access
2. **A Gemini API key** — free from [Google AI Studio](https://aistudio.google.com/apikey)
3. **Supabase credentials** (URL + service role key) — from your Supabase dashboard
4. **A domain name** (optional) — for automatic TLS via Caddy

Everything else (PostgreSQL, Qdrant, Redis, secrets) is set up automatically.

## One-Command Deploy

SSH into your VPS as root, then:

```bash
# Download and run the setup script
curl -O https://raw.githubusercontent.com/t0ttora/intel/main/setup-vps.sh
bash setup-vps.sh
```

The script will prompt you for:
- GitHub repo URL (this repo)
- Path to intel code inside repo (default: root `/`)
- Gemini API key
- Supabase URL and service key
- Sentry DSN (optional)
- Domain for TLS (optional)

It then automatically:
1. Creates a `noble` user with SSH key auth
2. Hardens SSH (disables root login)
3. Configures UFW firewall (ports 22, 80, 443 only)
4. Installs Fail2ban
5. Installs PostgreSQL 16 with optimized config + full schema
6. Installs Docker + Qdrant 1.13.2 with the `intel_signals` collection
7. Installs Redis 7 with password auth
8. Installs Python 3.12 + Playwright system deps
9. Clones the repo, creates a virtualenv, installs dependencies
10. Writes the `.env` with all auto-generated credentials
11. Installs Caddy reverse proxy (auto-TLS if domain provided)
12. Creates and starts 3 systemd services
13. Sets up log rotation and encrypted daily backups
14. Runs a health check

## What Gets Installed

| Service | Port | Binding | Purpose |
|---------|------|---------|---------|
| PostgreSQL 16 | 5432 | localhost | Signal storage |
| Qdrant 1.13.2 | 6333 | localhost | Vector search |
| Redis 7 | 6379 | localhost | Celery broker |
| Intel API (uvicorn) | 8000 | localhost | REST API |
| Caddy | 80, 443 | public | Reverse proxy + TLS |

All services except Caddy bind to localhost only — no direct public exposure.

## Systemd Services

| Service | Process | Memory Limit |
|---------|---------|-------------|
| `intel-api` | uvicorn (2 workers) | 512 MB |
| `intel-worker` | Celery worker (concurrency 2) | 1.5 GB |
| `intel-scheduler` | Celery beat | 256 MB |

### Commands

```bash
# Status
sudo systemctl status intel-api intel-worker intel-scheduler

# Restart all
sudo systemctl restart intel-api intel-worker intel-scheduler

# View logs
sudo journalctl -u intel-api -f
sudo journalctl -u intel-worker -f

# Or via Celery log files
tail -f /data/logs/celery-worker.log
tail -f /data/logs/celery-beat.log
```

## Updating

### Automatic (Recommended)

Every push to `main` that changes `docs/infrastructure/intel/**` triggers auto-deploy via GitHub Actions. See [ci-cd-auto-deploy.md](ci-cd-auto-deploy.md) for setup.

### Manual (Fallback)

```bash
# On the VPS, as noble user
/opt/noble-intel/update.sh https://github.com/YOUR_ORG/nobleverse.git docs/infrastructure/intel
```

This pulls the latest code, reinstalls the package, and restarts all services.

## Directory Layout on VPS

```
/opt/noble-intel/           # Application code
├── .env                    # Secrets (chmod 600)
├── .venv/                  # Python virtualenv
├── app/                    # Core application
├── cli/                    # NobleCLI
├── tests/                  # Test suite
├── backup.sh               # Daily backup script
└── update.sh               # Update script

/data/                      # Persistent data
├── postgres/               # PostgreSQL data (unused — uses default)
├── qdrant/                 # Qdrant storage
├── redis/                  # Redis data
├── cold/backups/           # Encrypted PG backups (7-day retention)
└── logs/                   # Application logs
    ├── caddy-access.log
    ├── celery-worker.log
    ├── celery-beat.log
    └── backup.log
```

## Security Measures

- **SSH**: key-only auth, root login disabled, max 3 attempts
- **Fail2ban**: 24h ban after 3 failures, 7-day ban for recidivists
- **UFW**: only ports 22, 80, 443 open
- **Services**: all bind to localhost except Caddy
- **API auth**: `X-API-Key` header required on all endpoints except /health
- **Rate limiting**: 30 req/min on `/api/v1/query`
- **Input sanitization**: prompt injection detection on all incoming signals
- **Systemd hardening**: `NoNewPrivileges`, `PrivateTmp`, `ProtectSystem=strict`  
- **Backups**: AES-256 encrypted, passphrase stored in `/etc/noble-backup-passphrase` (chmod 400)
- **Auto-updates**: Ubuntu unattended-upgrades for security patches

## Backups

Daily at 03:00 UTC:
- PostgreSQL full dump → gzip → AES-256 encrypt → `/data/cold/backups/`
- 7-day retention (older backups auto-deleted)

Qdrant snapshots (manual):
```bash
curl -X POST http://127.0.0.1:6333/collections/intel_signals/snapshots
```

## Monitoring

Built-in:
- `/health` endpoint for uptime monitoring
- `noblecli status` for full system overview
- Celery worker/beat logs at `/data/logs/`
- Sentry for error tracking (optional)

External (optional):
- Prometheus node-exporter at `localhost:9100`
- Qdrant metrics at `localhost:6333/metrics`
- Uptime Kuma via Docker for external health checks

## Resource Budget (CX33: 4 vCPU, 8 GB RAM)

| Component | RAM Budget |
|-----------|-----------|
| PostgreSQL | ~400 MB (256MB shared_buffers + overhead) |
| Qdrant | ~400 MB (with on_disk_payload) |
| Redis | 256 MB (maxmemory) |
| Intel API (2 workers) | ~512 MB |
| Celery worker (2 procs) | ~1 GB |
| Celery beat | ~128 MB |
| System + Caddy | ~500 MB |
| **Total** | **~3.2 GB** (leaves ~4.8 GB headroom) |

## Troubleshooting

### Services won't start
```bash
# Check logs
sudo journalctl -u intel-api --no-pager -n 50
sudo journalctl -u intel-worker --no-pager -n 50

# Common: .env permissions
ls -la /opt/noble-intel/.env
# Should be: -rw------- noble noble
```

### Qdrant not responding
```bash
docker ps | grep qdrant
docker logs qdrant --tail 20
# Restart:
docker restart qdrant
```

### Celery tasks not running
```bash
# Check Redis
redis-cli -a "$REDIS_PASSWORD" ping

# Check queue
redis-cli -a "$REDIS_PASSWORD" llen celery
```

### High memory usage
```bash
# Check per-service
systemctl status intel-worker  # shows memory usage
# The worker auto-restarts children at 500MB (--max-memory-per-child)
```
