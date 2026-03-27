# CI/CD Auto-Deploy Pipeline

Noble Intel auto-deploys to the VPS on every push to `main` that touches `docs/infrastructure/intel/**`. No manual SSH required after initial setup.

## How It Works

```
Developer pushes to main
  │
  ▼
GitHub Actions detects changes in docs/infrastructure/intel/**
  │
  ▼
deploy-intel.yml triggers
  │
  ▼
SSH into VPS as 'noble' user
  │
  ▼
git clone --depth 1 → rsync code (preserves .env, .venv, backup.sh, update.sh)
  │
  ▼
pip install -e . (rebuild package)
  │
  ▼
systemctl restart intel-api intel-worker intel-scheduler
  │
  ▼
Health check: curl http://127.0.0.1:8000/health
  │
  ├─ Pass → Deploy marked successful ✓
  └─ Fail → Deploy marked failed ✗ (services rollback to previous state)
```

## GitHub Actions Workflow

File: `.github/workflows/deploy-intel.yml`

```yaml
name: Deploy Intel

on:
  push:
    branches: [main]
    paths:
      - 'docs/infrastructure/intel/**'

jobs:
  deploy:
    name: Deploy to VPS
    runs-on: ubuntu-latest
    timeout-minutes: 5
    environment: intel-production

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.INTEL_VPS_HOST }}
          username: noble
          key: ${{ secrets.INTEL_VPS_SSH_KEY }}
          script: |
            set -euo pipefail
            cd /opt/noble-intel

            # Pull latest code
            TMPDIR=$(mktemp -d)
            git clone --depth 1 https://github.com/${{ github.repository }}.git "$TMPDIR/repo"

            # Sync code — preserve secrets and runtime artifacts
            rsync -a --delete \
              --exclude='.git' \
              --exclude='.env' \
              --exclude='.venv' \
              --exclude='setup-vps.sh' \
              --exclude='backup.sh' \
              --exclude='update.sh' \
              "$TMPDIR/repo/docs/infrastructure/intel/" /opt/noble-intel/

            rm -rf "$TMPDIR"

            # Reinstall package
            source .venv/bin/activate
            pip install -e . --quiet

            # Restart all services
            sudo systemctl restart intel-api intel-worker intel-scheduler

            # Health check (wait for startup)
            sleep 3
            curl -sf http://127.0.0.1:8000/health || exit 1
            echo "Deploy successful"
```

## Required GitHub Secrets

Set in **Settings → Environments → `intel-production`**:

| Secret | Value | How to get it |
|--------|-------|---------------|
| `INTEL_VPS_HOST` | VPS IP or domain (e.g. `intel.nobleverse.com`) | Your Hetzner dashboard |
| `INTEL_VPS_SSH_KEY` | Private SSH key (ed25519) for `noble` user | Generate with `ssh-keygen -t ed25519` |

## Setting Up Deploy Keys

```bash
# On your local machine — generate a dedicated deploy key
ssh-keygen -t ed25519 -C "intel-deploy" -f ~/.ssh/intel-deploy -N ""

# Add the PUBLIC key to the VPS noble user
ssh noble@YOUR_VPS_IP "cat >> ~/.ssh/authorized_keys" < ~/.ssh/intel-deploy.pub

# Add the PRIVATE key to GitHub
# Go to: GitHub → nobleverse repo → Settings → Secrets and variables → Actions
#   Name:  INTEL_VPS_SSH_KEY
#   Value: (paste contents of ~/.ssh/intel-deploy)
#
#   Name:  INTEL_VPS_HOST
#   Value: intel.nobleverse.com (or raw IP)
```

## What Gets Preserved on Deploy

These files are **never overwritten** during auto-deploy:

| File/Dir | Reason |
|----------|--------|
| `.env` | Contains generated secrets (DB password, API keys) |
| `.venv/` | Python virtualenv (rebuilt via `pip install -e .`) |
| `setup-vps.sh` | One-time provisioning script |
| `backup.sh` | Backup script with VPS-specific paths |
| `update.sh` | Manual update script (fallback) |

## Manual Deploy (Fallback)

If GitHub Actions fails or you need to deploy immediately:

```bash
# SSH into VPS as noble
ssh noble@intel.nobleverse.com

# Run the embedded update script
/opt/noble-intel/update.sh https://github.com/YOUR_ORG/nobleverse.git docs/infrastructure/intel
```

## Verifying a Deploy

```bash
# Check the deployed commit hash
curl -s https://intel.nobleverse.com/health | python3 -m json.tool
# Response includes "commit": "abc1234"

# Check service status
ssh noble@intel.nobleverse.com "sudo systemctl status intel-api intel-worker intel-scheduler"

# Check recent deploy logs
# In GitHub → Actions → Deploy Intel → most recent run
```

## Rollback

There is no automated rollback. If a bad deploy passes the health check but breaks functionality:

```bash
# SSH into VPS
ssh noble@intel.nobleverse.com

# Option 1: Revert to a specific commit
cd /opt/noble-intel
TMPDIR=$(mktemp -d)
git clone --depth 1 --branch <tag-or-sha> https://github.com/YOUR_ORG/nobleverse.git "$TMPDIR/repo"
rsync -a --delete \
  --exclude='.git' --exclude='.env' --exclude='.venv' \
  --exclude='setup-vps.sh' --exclude='backup.sh' --exclude='update.sh' \
  "$TMPDIR/repo/docs/infrastructure/intel/" /opt/noble-intel/
rm -rf "$TMPDIR"
source .venv/bin/activate
pip install -e . --quiet
sudo systemctl restart intel-api intel-worker intel-scheduler

# Option 2: Revert the commit on main and let CI/CD redeploy
git revert <bad-commit> && git push origin main
```
