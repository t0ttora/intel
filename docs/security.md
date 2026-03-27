# Security

Security architecture for Noble Intel VPS deployment.

## Security Layers

```
Internet
  │
  ├── UFW Firewall (ports 22, 80, 443 only)
  │
  ├── Fail2ban (SSH brute-force protection)
  │
  ├── Caddy (TLS termination, request size limit 1MB)
  │
  ├── API Key Authentication (X-API-Key header)
  │
  ├── Rate Limiting (30 req/min per key on /query)
  │
  ├── Input Sanitization (prompt injection detection)
  │
  └── Intel API (localhost:8000, never exposed directly)
```

## Network Security

### Firewall (UFW)

Only 3 ports are open to the internet:

| Port | Protocol | Purpose |
|------|----------|---------|
| 22 | TCP | SSH (key-only, noble user only) |
| 80 | TCP | HTTP (Caddy redirects to 443) |
| 443 | TCP | HTTPS (Caddy auto-TLS) |

All backend services bind to `127.0.0.1` only:

| Service | Port | Binding |
|---------|------|---------|
| PostgreSQL | 5432 | localhost |
| Qdrant | 6333, 6334 | 127.0.0.1 |
| Redis | 6379 | 127.0.0.1 |
| Intel API | 8000 | 127.0.0.1 |

### SSH Hardening

Configured in `/etc/ssh/sshd_config.d/hardening.conf`:

```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 2
X11Forwarding no
AllowUsers noble
```

### Fail2ban

| Jail | MaxRetry | BanTime | FindTime |
|------|----------|---------|----------|
| `sshd` | 3 | 24 hours | 10 min |
| `recidive` | 5 | 7 days | 24 hours |

## API Security

### Authentication

All endpoints except `/health` require an API key:

```
X-API-Key: <INTEL_API_KEY>
```

The key is generated during setup with `secrets.token_urlsafe(32)` (256 bits of entropy).

### Rate Limiting

| Endpoint | Limit | Window | Scope |
|----------|-------|--------|-------|
| `POST /api/v1/query` | 30 requests | 60 seconds | Per API key |

Implementation: in-memory per-worker counter. Resets on service restart. Each uvicorn worker maintains its own counter (effectively 60 req/min total across 2 workers).

### Input Validation

- Query text: Pydantic validation (3-500 chars)
- Risk scores: 0.0-1.0 range enforcement
- All request bodies validated with Pydantic `.parse()` at boundary

### Prompt Injection Protection

The `app/ingestion/sanitizer.py` module:
- Detects known injection patterns in incoming signals AND user queries
- Rejects queries with suspicious content (400 response)
- Sanitizes signal content before storage and embedding

### Error Handling

- Internal errors logged to Sentry with full stack trace
- Client receives only generic error: `{"error": "internal_server_error", "detail": "An unexpected error occurred"}`
- No stack traces, database details, or internal paths leaked to client

## Data Security

### Secrets Management

| Secret | Storage | Permissions |
|--------|---------|-------------|
| `.env` file | `/opt/noble-intel/.env` | `600 noble:noble` |
| Backup passphrase | `/etc/noble-backup-passphrase` | `400 root:root` |
| PostgreSQL password | In `.env` (DATABASE_URL) | Not in pg_hba.conf |
| Redis password | In Redis config + `.env` | requirepass directive |
| Qdrant API key | Docker env + `.env` | Container-scoped |

### Backup Encryption

Daily PostgreSQL backups are encrypted:

```
pg_dump → gzip → GPG AES-256 symmetric → /data/cold/backups/
```

- Passphrase: 384-bit random (`secrets.token_urlsafe(48)`)
- Retention: 7 days (auto-deleted)
- Passphrase stored in `/etc/noble-backup-passphrase` (root-only read)

### TLS

Caddy provides automatic TLS via Let's Encrypt:
- Auto-renewal before expiry
- HTTP → HTTPS redirect
- Modern cipher suites (Caddy defaults)

For IP-only mode (no domain), traffic is unencrypted on port 80. Use SSH tunnel for secure access:

```bash
ssh -L 8000:127.0.0.1:8000 noble@YOUR_VPS_IP
curl http://localhost:8000/health
```

## Systemd Hardening

All services run with:

```ini
NoNewPrivileges=true      # Cannot gain new privileges
PrivateTmp=true           # Isolated /tmp
ProtectSystem=strict      # Read-only filesystem except allowed paths
ProtectHome=true          # Cannot access /home
ReadWritePaths=/data/logs /opt/noble-intel  # Explicit write permissions
```

## Auto-Updates

Ubuntu `unattended-upgrades` is enabled for security patches. This applies OS-level security fixes automatically without touching the Intel application.

## Threat Model

| Threat | Mitigation |
|--------|-----------|
| Brute-force SSH | Key-only auth, Fail2ban (24h ban after 3 attempts) |
| API abuse | API key auth, rate limiting (30 req/min) |
| Prompt injection via signals | Sanitizer module, pattern detection |
| Prompt injection via queries | Query sanitization before pipeline |
| Data exfiltration | All services localhost-only, UFW |
| Unauthorized DB access | PostgreSQL password auth, localhost binding |
| Man-in-the-middle | Caddy auto-TLS (Let's Encrypt) |
| Credential leak | `.env` chmod 600, generic error responses |
| Supply chain (pip) | pinned versions in `pyproject.toml` |
| Backup theft | GPG AES-256 encryption |

## Known Limitations

1. **In-memory rate limiter** — resets on restart, per-worker counters. Sufficient for current scale. For stricter enforcement, migrate to Redis-backed rate limiting.
2. **Single API key** — all clients share one key. For multi-tenant access, add per-user keys with a `api_keys` table.
3. **No WAF** — Caddy does basic request size limiting (1MB). For advanced protection, add Cloudflare in front.
