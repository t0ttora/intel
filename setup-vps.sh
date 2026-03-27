#!/usr/bin/env bash
# ============================================================================
# Noble Intel v3.0 — VPS Setup Script
# Target: Ubuntu 24.04 LTS (Hetzner CX33 — 4 vCPU, 8 GB RAM)
#
# Usage:
#   1. Push the intel/ directory to a GitHub repo
#   2. SSH into a fresh Ubuntu 24.04 VPS as root
#   3. Run:  bash setup-vps.sh
#   4. Follow the prompts for secrets (Gemini key, Supabase creds, etc.)
#
# What this script does:
#   - Creates 'noble' user with sudo
#   - Hardens SSH (disables root login, password auth)
#   - Configures UFW firewall
#   - Installs Fail2ban
#   - Installs PostgreSQL 16 + creates schema
#   - Installs Docker + runs Qdrant 1.13.2
#   - Installs Redis 7 with auth
#   - Installs Python 3.12 + Playwright deps
#   - Clones your repo + installs noble-intel in a venv
#   - Installs Caddy reverse proxy
#   - Creates systemd services (API, worker, beat)
#   - Sets up log rotation + daily backup cron
#   - Runs a verification health check
# ============================================================================
set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; }
step() { echo -e "\n${BLUE}${BOLD}══════════════════════════════════════════${NC}"; echo -e "${BLUE}${BOLD}  $1${NC}"; echo -e "${BLUE}${BOLD}══════════════════════════════════════════${NC}\n"; }

# ── Pre-flight checks ──────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    err "This script must be run as root."
    exit 1
fi

if ! grep -q "Ubuntu" /etc/os-release 2>/dev/null; then
    err "This script is designed for Ubuntu 24.04 LTS."
    exit 1
fi

# ── Collect required input ──────────────────────────────────────────────────
step "1/16  Collect Configuration"

read -rp "GitHub repo URL (HTTPS clone URL): " GITHUB_REPO
if [[ -z "$GITHUB_REPO" ]]; then
    err "GitHub repo URL is required."
    exit 1
fi

# Path inside the repo where intel/ code lives (default: docs/infrastructure/intel)
read -rp "Path to intel code inside repo [docs/infrastructure/intel]: " INTEL_PATH
INTEL_PATH="${INTEL_PATH:-docs/infrastructure/intel}"

read -rp "Gemini API key: " GEMINI_API_KEY
if [[ -z "$GEMINI_API_KEY" ]]; then
    err "Gemini API key is required."
    exit 1
fi

read -rp "Supabase URL (e.g. https://xxx.supabase.co): " SUPABASE_URL
read -rp "Supabase service role key: " SUPABASE_SERVICE_KEY
read -rp "Sentry DSN (leave blank to skip): " SENTRY_DSN
read -rp "Domain for TLS (leave blank for IP-only mode): " DOMAIN

echo ""
log "Configuration collected. Generating secrets..."

# ── Generate secrets ────────────────────────────────────────────────────────
PG_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
REDIS_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
QDRANT_API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
INTEL_API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
BACKUP_PASSPHRASE=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")

# Save secrets to a temporary file the operator can copy
SECRETS_FILE="/root/.noble-intel-secrets"
cat > "$SECRETS_FILE" << SECRETS
# Noble Intel — Generated Secrets ($(date -Iseconds))
# SAVE THESE IN YOUR PASSWORD MANAGER, THEN DELETE THIS FILE
PG_PASSWORD=$PG_PASSWORD
REDIS_PASSWORD=$REDIS_PASSWORD
QDRANT_API_KEY=$QDRANT_API_KEY
INTEL_API_KEY=$INTEL_API_KEY
BACKUP_PASSPHRASE=$BACKUP_PASSPHRASE
SECRETS
chmod 600 "$SECRETS_FILE"
log "Secrets saved to $SECRETS_FILE — copy them to your password manager"

# ── System update ───────────────────────────────────────────────────────────
step "2/16  System Update"

export DEBIAN_FRONTEND=noninteractive
apt update
apt upgrade -y
apt install -y \
    ca-certificates curl gnupg lsb-release \
    git build-essential software-properties-common \
    unattended-upgrades
log "System updated"

# ── Create noble user ──────────────────────────────────────────────────────
step "3/16  Create 'noble' User"

if id "noble" &>/dev/null; then
    warn "User 'noble' already exists, skipping"
else
    adduser --disabled-password --gecos "Noble Intel" noble
    usermod -aG sudo noble
    # Allow sudo without password for setup; tighten later if desired
    echo "noble ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/noble
    chmod 440 /etc/sudoers.d/noble

    # Copy SSH keys from root
    mkdir -p /home/noble/.ssh
    if [[ -f /root/.ssh/authorized_keys ]]; then
        cp /root/.ssh/authorized_keys /home/noble/.ssh/
    fi
    chown -R noble:noble /home/noble/.ssh
    chmod 700 /home/noble/.ssh
    chmod 600 /home/noble/.ssh/authorized_keys 2>/dev/null || true
    log "User 'noble' created with SSH keys"
fi

# ── SSH hardening ───────────────────────────────────────────────────────────
step "4/16  SSH Hardening"

cat > /etc/ssh/sshd_config.d/hardening.conf << 'EOF'
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 2
X11Forwarding no
AllowUsers noble
EOF

systemctl restart sshd
log "SSH hardened (root login disabled, key-only auth)"
warn "TEST SSH as 'noble' FROM ANOTHER TERMINAL before closing this session!"

# ── Firewall ────────────────────────────────────────────────────────────────
step "5/16  UFW Firewall"

ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP (Caddy redirect)
ufw allow 443/tcp  # HTTPS (Caddy)
ufw --force enable
log "Firewall configured (22, 80, 443 open)"

# ── Fail2ban ────────────────────────────────────────────────────────────────
step "6/16  Fail2ban"

apt install -y fail2ban

cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
ignoreip = 127.0.0.1/8 ::1
bantime = 86400
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = 22

[recidive]
enabled = true
logpath = /var/log/fail2ban.log
banaction = iptables-allports
bantime = 604800
findtime = 86400
maxretry = 5
EOF

systemctl enable fail2ban
systemctl restart fail2ban
log "Fail2ban configured (SSH + recidive jails)"

# ── Data directories ───────────────────────────────────────────────────────
step "7/16  Data Directories"

mkdir -p /data/{postgres,qdrant,redis,cold/backups,logs}
chown -R noble:noble /data
log "Created /data/{postgres,qdrant,redis,cold,logs}"

# ── PostgreSQL 16 ──────────────────────────────────────────────────────────
step "8/16  PostgreSQL 16"

apt install -y postgresql-16 postgresql-client-16

cat > /etc/postgresql/16/main/conf.d/noble.conf << 'EOF'
listen_addresses = 'localhost'
ssl = on
shared_buffers = 256MB
work_mem = 8MB
maintenance_work_mem = 128MB
effective_cache_size = 4GB
wal_buffers = 16MB
checkpoint_completion_target = 0.9
max_connections = 50
log_min_duration_statement = 500
log_line_prefix = '%t [%p] %u@%d '
EOF

systemctl restart postgresql

# Create user + database + schema
sudo -u postgres psql << PGSETUP
CREATE USER noble WITH PASSWORD '${PG_PASSWORD}';
CREATE DATABASE noble_intel OWNER noble;
\\c noble_intel
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;
PGSETUP

sudo -u postgres psql noble_intel << 'SCHEMA'
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
    ('imo', 0.95, 0.95, 0.85, 1.00),
    ('ukmto', 0.95, 0.95, 0.85, 1.00),
    ('carrier_direct', 0.85, 0.85, 0.70, 0.95),
    ('ais', 0.80, 0.80, 0.70, 0.95),
    ('freight_index', 0.80, 0.80, 0.70, 0.90),
    ('tier1_news', 0.70, 0.70, 0.50, 0.85),
    ('general_news', 0.65, 0.65, 0.45, 0.80),
    ('reddit', 0.40, 0.40, 0.15, 0.70),
    ('twitter', 0.35, 0.35, 0.10, 0.65),
    ('linkedin', 0.45, 0.45, 0.20, 0.70)
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

log "PostgreSQL 16 installed, noble_intel database + schema created"

# ── Docker + Qdrant ─────────────────────────────────────────────────────────
step "9/16  Docker + Qdrant 1.13.2"

# Install Docker via official APT repo
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
usermod -aG docker noble

# Run Qdrant (localhost only)
docker rm -f qdrant 2>/dev/null || true
docker run -d \
    --name qdrant \
    --restart unless-stopped \
    -p 127.0.0.1:6333:6333 \
    -p 127.0.0.1:6334:6334 \
    -v /data/qdrant:/qdrant/storage \
    -e QDRANT__SERVICE__MAX_REQUEST_SIZE_MB=10 \
    -e "QDRANT__SERVICE__API_KEY=${QDRANT_API_KEY}" \
    qdrant/qdrant:v1.13.2

# Wait for Qdrant to be ready
echo -n "Waiting for Qdrant..."
for i in {1..30}; do
    if curl -sf http://127.0.0.1:6333/healthz > /dev/null 2>&1; then
        echo " ready"
        break
    fi
    echo -n "."
    sleep 2
done

# Create the intel_signals collection
curl -sf -X PUT http://127.0.0.1:6333/collections/intel_signals \
    -H "api-key: ${QDRANT_API_KEY}" \
    -H 'Content-Type: application/json' \
    -d '{
        "vectors": { "size": 768, "distance": "Cosine" },
        "optimizers_config": { "memmap_threshold": 20000 },
        "on_disk_payload": true
    }' > /dev/null

log "Qdrant 1.13.2 running, intel_signals collection created (768-dim Cosine)"

# ── Redis 7 ─────────────────────────────────────────────────────────────────
step "10/16  Redis 7"

apt install -y redis-server

# Configure: localhost only, password, memory limit
sed -i 's/^bind .*/bind 127.0.0.1 ::1/' /etc/redis/redis.conf
sed -i 's/^# maxmemory .*/maxmemory 256mb/' /etc/redis/redis.conf
sed -i 's/^# maxmemory-policy .*/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf

# Remove any existing requirepass lines, then add ours
sed -i '/^requirepass /d' /etc/redis/redis.conf
echo "requirepass ${REDIS_PASSWORD}" >> /etc/redis/redis.conf

systemctl restart redis-server
systemctl enable redis-server
log "Redis 7 installed (localhost, password auth, 256MB limit)"

# ── Python 3.12 + dependencies ─────────────────────────────────────────────
step "11/16  Python 3.12 + Playwright"

apt install -y python3.12 python3.12-venv python3.12-dev python3-pip

# Playwright system dependencies
apt install -y \
    libnss3 libnspr4 libatk1.0-0t64 libatk-bridge2.0-0t64 \
    libcups2t64 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2t64 \
    2>/dev/null || \
apt install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 \
    2>/dev/null || true

log "Python 3.12 + system dependencies installed"

# ── Clone repo + install ───────────────────────────────────────────────────
step "12/16  Clone Repo + Install"

INSTALL_DIR="/opt/noble-intel"
mkdir -p "$INSTALL_DIR"
chown noble:noble "$INSTALL_DIR"

# Clone to a temp dir, then copy intel code to /opt/noble-intel
TMPDIR=$(mktemp -d)
git clone --depth 1 "$GITHUB_REPO" "$TMPDIR/repo"

if [[ ! -d "$TMPDIR/repo/$INTEL_PATH" ]]; then
    err "Path '$INTEL_PATH' not found in the cloned repo."
    err "Contents of repo root:"
    ls -la "$TMPDIR/repo/"
    rm -rf "$TMPDIR"
    exit 1
fi

# Copy intel code into /opt/noble-intel (preserving structure)
rsync -a --delete \
    --exclude='.git' \
    --exclude='setup-vps.sh' \
    --exclude='README.md' \
    --exclude='.env.example' \
    "$TMPDIR/repo/$INTEL_PATH/" "$INSTALL_DIR/"

rm -rf "$TMPDIR"
chown -R noble:noble "$INSTALL_DIR"

# Create venv and install as noble user
sudo -u noble bash << 'VENV_SETUP'
cd /opt/noble-intel
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install -e .
pip install -e ".[dev]"
VENV_SETUP

# Install Playwright Chromium browser
sudo -u noble bash -c "cd /opt/noble-intel && source .venv/bin/activate && playwright install chromium"

log "Repo cloned, venv created, noble-intel installed"

# ── Write .env ──────────────────────────────────────────────────────────────
step "13/16  Environment Configuration"

cat > "$INSTALL_DIR/.env" << ENVFILE
# === Noble Intel v3.0 — Generated $(date -Iseconds) ===

# Gemini
GEMINI_API_KEY=${GEMINI_API_KEY}

# PostgreSQL
DATABASE_URL=postgresql://noble:${PG_PASSWORD}@127.0.0.1:5432/noble_intel

# Qdrant
QDRANT_URL=http://127.0.0.1:6333
QDRANT_API_KEY=${QDRANT_API_KEY}
QDRANT_COLLECTION=intel_signals

# Redis
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=redis://:${REDIS_PASSWORD}@127.0.0.1:6379/0

# Supabase
SUPABASE_URL=${SUPABASE_URL}
SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}

# Intel API
INTEL_API_KEY=${INTEL_API_KEY}
INTEL_API_PORT=8000

# Sentry
SENTRY_DSN=${SENTRY_DSN}
ENVFILE

chmod 600 "$INSTALL_DIR/.env"
chown noble:noble "$INSTALL_DIR/.env"
log ".env written to $INSTALL_DIR/.env"

# ── Caddy reverse proxy ────────────────────────────────────────────────────
step "14/16  Caddy Reverse Proxy"

apt install -y caddy

if [[ -n "$DOMAIN" ]]; then
    cat > /etc/caddy/Caddyfile << CADDYEOF
${DOMAIN} {
    reverse_proxy 127.0.0.1:8000

    request_body {
        max_size 1MB
    }

    log {
        output file /data/logs/caddy-access.log
        format json
    }
}
CADDYEOF
    log "Caddy configured for ${DOMAIN} with auto-TLS"
else
    cat > /etc/caddy/Caddyfile << 'CADDYEOF'
:80 {
    reverse_proxy 127.0.0.1:8000

    request_body {
        max_size 1MB
    }

    log {
        output file /data/logs/caddy-access.log
        format json
    }
}
CADDYEOF
    warn "No domain set — Caddy configured on port 80 (no TLS). Add a domain later."
fi

systemctl enable caddy
systemctl restart caddy
log "Caddy installed and running"

# ── Systemd services ───────────────────────────────────────────────────────
step "15/16  Systemd Services"

# --- intel-api ---
cat > /etc/systemd/system/intel-api.service << 'EOF'
[Unit]
Description=Noble Intel REST API
After=network.target postgresql.service redis-server.service
Wants=postgresql.service redis-server.service

[Service]
Type=exec
User=noble
Group=noble
WorkingDirectory=/opt/noble-intel
EnvironmentFile=/opt/noble-intel/.env
ExecStart=/opt/noble-intel/.venv/bin/uvicorn app.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 2 \
    --limit-max-requests 10000 \
    --timeout-keep-alive 30
Restart=always
RestartSec=5
MemoryMax=512M
CPUQuota=100%
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/data/logs /opt/noble-intel

[Install]
WantedBy=multi-user.target
EOF

# --- intel-worker ---
cat > /etc/systemd/system/intel-worker.service << 'EOF'
[Unit]
Description=Noble Intel Celery Workers
After=network.target redis-server.service postgresql.service

[Service]
Type=exec
User=noble
Group=noble
WorkingDirectory=/opt/noble-intel
EnvironmentFile=/opt/noble-intel/.env
ExecStart=/opt/noble-intel/.venv/bin/celery -A app.tasks.celery_app worker \
    --concurrency=2 \
    --max-memory-per-child=500000 \
    --loglevel=info \
    --logfile=/data/logs/celery-worker.log
Restart=always
RestartSec=10
MemoryMax=1536M
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/data/logs /opt/noble-intel

[Install]
WantedBy=multi-user.target
EOF

# --- intel-scheduler ---
cat > /etc/systemd/system/intel-scheduler.service << 'EOF'
[Unit]
Description=Noble Intel Celery Beat Scheduler
After=network.target redis-server.service

[Service]
Type=exec
User=noble
Group=noble
WorkingDirectory=/opt/noble-intel
EnvironmentFile=/opt/noble-intel/.env
ExecStart=/opt/noble-intel/.venv/bin/celery -A app.tasks.celery_app beat \
    --loglevel=info \
    --logfile=/data/logs/celery-beat.log
Restart=always
RestartSec=10
MemoryMax=256M

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable intel-api intel-worker intel-scheduler
systemctl start intel-api intel-worker intel-scheduler
log "Systemd services created and started (intel-api, intel-worker, intel-scheduler)"

# ── Log rotation + backups ──────────────────────────────────────────────────
step "16/16  Log Rotation + Backups"

# Log rotation
cat > /etc/logrotate.d/noble-intel << 'EOF'
/data/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF

# Backup passphrase
echo -n "$BACKUP_PASSPHRASE" > /etc/noble-backup-passphrase
chmod 400 /etc/noble-backup-passphrase
chown root:root /etc/noble-backup-passphrase

# Backup script
cat > /opt/noble-intel/backup.sh << 'BACKUP'
#!/bin/bash
set -euo pipefail
BACKUP_DIR="/data/cold/backups"
mkdir -p "$BACKUP_DIR"

pg_dump -U noble noble_intel \
  | gzip \
  | gpg --batch --symmetric --cipher-algo AES256 \
        --passphrase-file /etc/noble-backup-passphrase \
  > "$BACKUP_DIR/pg_$(date +%Y%m%d).sql.gz.gpg"

find "$BACKUP_DIR" -name "pg_*.sql.gz.gpg" -mtime +7 -delete
echo "[$(date)] Backup complete" >> /data/logs/backup.log
BACKUP
chmod +x /opt/noble-intel/backup.sh
chown noble:noble /opt/noble-intel/backup.sh

# Daily backup cron at 3 AM
echo "0 3 * * * noble /opt/noble-intel/backup.sh" > /etc/cron.d/noble-backup
chmod 644 /etc/cron.d/noble-backup

# Unattended upgrades
dpkg-reconfigure -plow unattended-upgrades 2>/dev/null || true

log "Log rotation, backups, and auto-updates configured"

# ── Update script ───────────────────────────────────────────────────────────
# Create a handy update script for future deploys
cat > /opt/noble-intel/update.sh << 'UPDATE'
#!/bin/bash
# Pull latest code from GitHub and restart services
set -euo pipefail

REPO_URL=$(git -C /tmp/noble-intel-update remote get-url origin 2>/dev/null || echo "")
INTEL_PATH="${INTEL_PATH:-docs/infrastructure/intel}"

echo "Updating Noble Intel..."

TMPDIR=$(mktemp -d)
git clone --depth 1 "$1" "$TMPDIR/repo" 2>/dev/null || {
    echo "Usage: ./update.sh <github-repo-url> [intel-path]"
    rm -rf "$TMPDIR"
    exit 1
}

IPATH="${2:-docs/infrastructure/intel}"

rsync -a --delete \
    --exclude='.git' \
    --exclude='.env' \
    --exclude='.venv' \
    --exclude='setup-vps.sh' \
    --exclude='backup.sh' \
    --exclude='update.sh' \
    "$TMPDIR/repo/$IPATH/" /opt/noble-intel/

rm -rf "$TMPDIR"

cd /opt/noble-intel
source .venv/bin/activate
pip install -e . --quiet

sudo systemctl restart intel-api intel-worker intel-scheduler
echo "Update complete. Services restarted."
UPDATE
chmod +x /opt/noble-intel/update.sh
chown noble:noble /opt/noble-intel/update.sh

# ── Verification ────────────────────────────────────────────────────────────
echo ""
echo ""
step "Verification Health Check"

echo -e "${BOLD}Services:${NC}"
for svc in postgresql redis-server intel-api intel-worker intel-scheduler caddy; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        echo -e "  ${GREEN}●${NC} $svc"
    else
        echo -e "  ${RED}●${NC} $svc (not running)"
    fi
done

echo ""
echo -e "${BOLD}PostgreSQL:${NC}"
sudo -u postgres psql noble_intel -t -c "SELECT 'source_weights: ' || count(*) FROM source_weights;" 2>/dev/null || echo "  (check failed)"

echo ""
echo -e "${BOLD}Qdrant:${NC}"
curl -sf http://127.0.0.1:6333/collections/intel_signals \
    -H "api-key: ${QDRANT_API_KEY}" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Collection: {d[\"result\"][\"status\"]}, vectors: {d[\"result\"][\"points_count\"]}')" \
    2>/dev/null || echo "  (check failed)"

echo ""
echo -e "${BOLD}Redis:${NC}"
redis-cli -a "$REDIS_PASSWORD" --no-auth-warning ping 2>/dev/null || echo "  (check failed)"

echo ""
echo -e "${BOLD}Intel API:${NC}"
sleep 3  # Give uvicorn a moment
curl -sf http://127.0.0.1:8000/health 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "  (starting up — check again in a few seconds)"

echo ""
echo ""
echo -e "${GREEN}${BOLD}══════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  Noble Intel v3.0 — Setup Complete${NC}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}API:${NC}        http://127.0.0.1:8000/health"
if [[ -n "$DOMAIN" ]]; then
    echo -e "  ${BOLD}Public:${NC}     https://${DOMAIN}/health"
fi
echo -e "  ${BOLD}API Key:${NC}    ${INTEL_API_KEY}"
echo -e "  ${BOLD}Secrets:${NC}    ${SECRETS_FILE}"
echo -e "  ${BOLD}Install:${NC}    ${INSTALL_DIR}"
echo -e "  ${BOLD}Logs:${NC}       /data/logs/"
echo ""
echo -e "  ${BOLD}CLI (on VPS):${NC}"
echo -e "    source /opt/noble-intel/.venv/bin/activate"
echo -e "    noblecli status"
echo -e "    noblecli query \"What is happening at the Suez Canal?\""
echo ""
echo -e "  ${BOLD}CLI (remote from MacBook):${NC}"
if [[ -n "$DOMAIN" ]]; then
    echo -e "    export NOBLE_INTEL_URL=https://${DOMAIN}"
else
    echo -e "    export NOBLE_INTEL_URL=http://<your-vps-ip>"
fi
echo -e "    export INTEL_API_KEY=${INTEL_API_KEY}"
echo -e "    noblecli status"
echo ""
echo -e "  ${BOLD}Update later:${NC}"
echo -e "    sudo -u noble /opt/noble-intel/update.sh ${GITHUB_REPO} ${INTEL_PATH}"
echo ""
echo -e "  ${YELLOW}IMPORTANT:${NC} Save secrets from ${SECRETS_FILE}, then delete it."
echo -e "  ${YELLOW}IMPORTANT:${NC} Test SSH as 'noble' before closing this root session!"
echo ""
