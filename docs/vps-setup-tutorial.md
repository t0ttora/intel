# VPS Setup Tutorial

Complete guide for connecting to and provisioning your VPS from a Mac. After this one-time setup, all future deployments are automatic on every `git push`.

---

## Part 1: Connect to Your VPS from Mac

Mac has SSH built in — no extra software needed.

### 1.1 Find your VPS IP

Log in to your Hetzner Cloud dashboard at [console.hetzner.cloud](https://console.hetzner.cloud). Your server's IP address is listed on the server overview page. It looks like `65.21.x.x`.

### 1.2 Generate an SSH key (if you don't have one)

Open Terminal on your Mac (`Cmd+Space` → type "Terminal"):

```bash
# Check if you already have a key
ls ~/.ssh/id_ed25519.pub
```

If that file exists, you already have a key — skip to step 1.3.

If not, generate one:

```bash
ssh-keygen -t ed25519 -C "your@email.com"
# Press Enter three times to accept defaults (no passphrase is fine for now)
```

This creates two files:
- `~/.ssh/id_ed25519` — private key (never share this)
- `~/.ssh/id_ed25519.pub` — public key (safe to share)

### 1.3 Add your SSH key to the VPS

Hetzner lets you add SSH keys when creating the server. If you added your key during server creation, skip to step 1.4.

If not, use the Hetzner rescue console to add it:
1. In Hetzner console → your server → "Networking" → "SSH Keys" → Add your public key
2. Or use the root password from the setup email to log in once and paste the key manually

### 1.4 SSH into the VPS

```bash
ssh root@YOUR_VPS_IP
# Example: ssh root@65.21.100.200
```

The first time, Terminal will warn: "The authenticity of host can't be established." Type `yes` and press Enter.

You should see a Linux command prompt like `root@ubuntu-server:~#`.

> **Tip**: Keep this Terminal window open. Open a second Terminal window for your local Mac commands during setup.

---

## Part 2: Before Running Setup — Gather Your Credentials

Have these ready before running the setup script. Open them in a browser tab:

| What | Where to get it |
|------|----------------|
| **GitHub repo URL** | Your nobleverse repo on GitHub → green "Code" button → HTTPS URL. Looks like `https://github.com/YOUR_USERNAME/nobleverse.git` |
| **Gemini API key** | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) → "Create API key" → copy it |
| **Supabase URL** | [supabase.com/dashboard](https://supabase.com/dashboard) → your project → Settings → API → "Project URL" |
| **Supabase service key** | Same page → "service_role" key (under "Project API keys") — click the eye icon to reveal |
| **Domain (optional)** | If you have a domain, decide on a subdomain like `intel.nobleverse.com`. If not, you can use the raw IP. |

---

## Part 3: DNS Setup (Only if Using a Domain)

If you want `https://intel.nobleverse.com` (with TLS), you need to point a DNS record at your VPS before running setup.

Go to wherever you manage your domain's DNS (Cloudflare, Namecheap, GoDaddy, etc.) and add:

```
Type:  A
Name:  intel          (makes intel.nobleverse.com)
Value: YOUR_VPS_IP
TTL:   Auto (or 3600)
```

Wait 5–10 minutes for it to propagate. You can check it worked:

```bash
# On your Mac
ping intel.nobleverse.com
# Should show your VPS IP in the response
```

If you don't have a domain, leave the domain prompt blank during setup — the API will be accessible on plain HTTP via the IP. You can add a domain later.

---

## Part 4: Run the Setup Script

Switch back to your SSH Terminal window (logged in as root on the VPS).

```bash
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/nobleverse/main/docs/infrastructure/intel/setup-vps.sh
bash setup-vps.sh
```

The script will ask you several questions. Here's what to enter:

```
GitHub repo URL (HTTPS clone URL):
→ https://github.com/YOUR_USERNAME/nobleverse.git

Path to intel code inside repo [docs/infrastructure/intel]:
→ (just press Enter — the default is correct)

Gemini API key:
→ AIzaSy... (paste your key from AI Studio)

Supabase URL (e.g. https://xxx.supabase.co):
→ https://abcdefgh.supabase.co

Supabase service role key:
→ eyJhbGci... (paste the service_role key)

Sentry DSN (leave blank to skip):
→ (press Enter to skip)

Domain for TLS (leave blank for IP-only mode):
→ intel.nobleverse.com   (or just press Enter to use raw IP)
```

After you answer those questions, the script runs fully automatically. It takes about **10–15 minutes** — PostgreSQL, Docker, Python, Playwright, and everything else installs without any more input from you.

The 16 automated steps:

| Step | What happens |
|------|-------------|
| 1/16 | Collect config, auto-generate 5 random secrets |
| 2/16 | `apt upgrade` — latest Ubuntu packages |
| 3/16 | Create `noble` user, copy your SSH keys to it |
| 4/16 | Disable root SSH login, enforce key-only auth |
| 5/16 | UFW firewall — only ports 22, 80, 443 open |
| 6/16 | Fail2ban — auto-ban brute-force attempts |
| 7/16 | Create `/data/` directories for persistent storage |
| 8/16 | PostgreSQL 16 — install, create DB, run full schema |
| 9/16 | Docker + Qdrant 1.13.2 — vector database |
| 10/16 | Redis 7 — task queue for background jobs |
| 11/16 | Python 3.12 + Playwright browser dependencies |
| 12/16 | Clone your repo, create Python venv, `pip install` |
| 13/16 | Write `.env` with all credentials and generated keys |
| 14/16 | Caddy reverse proxy — auto-TLS if domain was set |
| 15/16 | Create and start 3 systemd services |
| 16/16 | Log rotation, daily encrypted backups, auto-updates |

---

## Part 5: Critical — Do This Before the Window Closes

**The script disables root SSH login as part of hardening.** Before you close anything, verify you can still get in.

Open a **new Terminal window** on your Mac (keep the root session open):

```bash
# In the NEW terminal window, try SSH as the 'noble' user
ssh noble@YOUR_VPS_IP
```

If this works, you're safe. If it fails, go back to your root session and check:

```bash
cat /home/noble/.ssh/authorized_keys
# Should contain your public key
```

---

## Part 6: Save Your Generated Secrets

The script saved all auto-generated secrets to a file on the VPS. **Read and save these now** — you cannot recover them later.

In your SSH session (root or noble):

```bash
cat /root/.noble-intel-secrets
```

You'll see something like:
```
PG_PASSWORD=xK9mP...       # PostgreSQL password
REDIS_PASSWORD=aB3nQ...    # Redis password
QDRANT_API_KEY=rT7wL...    # Qdrant authentication
INTEL_API_KEY=zP2vH...     # This goes into NextJS .env as NOBLE_INTEL_KEY
BACKUP_PASSPHRASE=yM...    # GPG passphrase for daily backups
```

**The most important one is `INTEL_API_KEY`** — you'll need it for the NextJS `.env` in a moment.

1. Copy all 5 values into your password manager (1Password, Bitwarden, Notes — anywhere secure)
2. Then delete the file:

```bash
rm /root/.noble-intel-secrets
```

---

## Part 7: Verify Everything Is Working

Still in your SSH session (as `noble`):

```bash
# Check all 3 services are running
sudo systemctl status intel-api intel-worker intel-scheduler
# All three should show: Active: active (running)

# Quick health check
curl http://127.0.0.1:8000/health
# Should return: {"status":"ok","version":"3.0.0","uptime_seconds":...}
```

If you set up a domain, test from your Mac:

```bash
# In your local Mac terminal
curl https://intel.nobleverse.com/health

# Then test a real query (replace YOUR_INTEL_API_KEY with the key you saved)
curl -X POST https://intel.nobleverse.com/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_INTEL_API_KEY" \
  -d '{"query": "What are the current risks at Suez Canal?"}'
```

The first query might return limited data — that's normal. Background tasks start ingesting immediately, but need ~1 hour to populate meaningful data.

---

## Part 8: Connect NextJS to the Intel API

On your Mac, open the NobleVerse `.env` file and add:

```env
# Intel API connection
NOBLE_INTEL_URL=https://intel.nobleverse.com
NOBLE_INTEL_KEY=<paste INTEL_API_KEY from the secrets file>
```

If you used IP-only mode (no domain):
```env
NOBLE_INTEL_URL=http://YOUR_VPS_IP
NOBLE_INTEL_KEY=<paste INTEL_API_KEY>
```

Then implement the tool handler — see [nextjs-integration.md](nextjs-integration.md).

---

## Part 9: Set Up Auto-Deploy

So that every future `git push` deploys automatically without you SSHing anywhere.

Run these commands on your **Mac** (not the VPS):

```bash
# Generate a dedicated deploy key (separate from your personal SSH key)
ssh-keygen -t ed25519 -C "intel-deploy" -f ~/.ssh/intel-deploy -N ""

# Add the public key to the VPS
ssh noble@YOUR_VPS_IP "cat >> ~/.ssh/authorized_keys" < ~/.ssh/intel-deploy.pub

# Print the private key — you'll paste this into GitHub
cat ~/.ssh/intel-deploy
```

Now go to GitHub:
1. Open your `nobleverse` repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add:
   - Name: `INTEL_VPS_SSH_KEY` → Value: (paste the private key output from above, including the `-----BEGIN...` and `-----END...` lines)
   - Name: `INTEL_VPS_HOST` → Value: `intel.nobleverse.com` (or your raw IP)

Then you need to create the workflow file — see [ci-cd-auto-deploy.md](ci-cd-auto-deploy.md) for the full `deploy-intel.yml` to add to `.github/workflows/`.

Test it by making any small change to a file in `docs/infrastructure/intel/` and pushing to `main`. The Actions tab on GitHub will show the deploy running.

---

## Post-Setup Checklist

```
[ ] SSH as noble works
[ ] Root SSH is disabled (cannot ssh root@...)
[ ] All 3 services running: intel-api, intel-worker, intel-scheduler
[ ] /health returns 200
[ ] /api/v1/query returns a response
[ ] TLS certificate active — https:// works (if domain set)
[ ] Secrets saved to password manager
[ ] /root/.noble-intel-secrets deleted from VPS
[ ] NOBLE_INTEL_URL + NOBLE_INTEL_KEY added to NextJS .env
[ ] GitHub deploy secrets (INTEL_VPS_HOST, INTEL_VPS_SSH_KEY) configured
[ ] deploy-intel.yml created in .github/workflows/
[ ] Auto-deploy tested with a test push to main
```

---

## Reconnecting Later

After setup, root login is disabled. Always connect as `noble`:

```bash
ssh noble@YOUR_VPS_IP
# or
ssh noble@intel.nobleverse.com
```

If you want a shortcut, add this to `~/.ssh/config` on your Mac:

```
Host intel
  HostName intel.nobleverse.com
  User noble
  IdentityFile ~/.ssh/id_ed25519
```

Then you can just type:

```bash
ssh intel
```

---

## Directory Layout After Setup

```
/opt/noble-intel/              # Application code (deployed here)
  ├── .env                     # All secrets (chmod 600)
  ├── .venv/                   # Python 3.12 virtualenv
  ├── app/                     # FastAPI application
  ├── cli/                     # NobleCLI
  ├── tests/                   # Test suite
  ├── backup.sh                # Daily encrypted PG backup
  └── update.sh                # Manual update fallback

/data/                         # Persistent data (survives redeploys)
  ├── qdrant/                  # Qdrant vector storage
  ├── redis/                   # Redis data
  ├── cold/backups/            # Encrypted PG dumps (7-day retention)
  └── logs/                    # Application logs
```

---

## Troubleshooting

### "Permission denied" when SSHing
Your SSH key isn't on the VPS. Use the Hetzner Cloud Console (browser-based terminal) to log in and add your public key to `/home/noble/.ssh/authorized_keys`.

```bash
# Print your public key on your Mac
cat ~/.ssh/id_ed25519.pub
# Copy the output, then paste it into the Hetzner console
```

### Services not starting
```bash
# Check logs
sudo journalctl -u intel-api --no-pager -n 50

# Most common cause: .env file permissions
ls -la /opt/noble-intel/.env
# Must be: -rw------- 1 noble noble
sudo chmod 600 /opt/noble-intel/.env
sudo chown noble:noble /opt/noble-intel/.env
sudo systemctl restart intel-api
```

### Qdrant not responding
```bash
docker ps | grep qdrant          # Should show "Up"
docker logs qdrant --tail 20     # Check for errors
docker restart qdrant            # Restart if needed
```

### TLS certificate not working
```bash
sudo journalctl -u caddy --no-pager -n 20
# Common: DNS not propagated yet — check with: dig intel.nobleverse.com
# Or: port 80/443 blocked
sudo ufw status
```

### Database connection refused
```bash
sudo systemctl status postgresql
sudo -u postgres psql -c "SELECT 1;"
```
