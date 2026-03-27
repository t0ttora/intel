# ADR-001: Deploy Intel from Separate Repository

**Status**: Accepted  
**Date**: 2026-03-27  
**Deciders**: Engineering team

## Context

Noble Intel is a Python FastAPI service that runs on a dedicated VPS. Initially it lived at `docs/infrastructure/intel/` inside the main NobleVerse monorepo. It has been extracted to its own repository at `https://github.com/t0ttora/intel`.

## Decision Drivers

- Independent deployment cycle (push to intel repo → auto-deploy, no noise in nobleverse CI)
- Clean repo boundaries — Python service separate from NextJS app
- Simpler CI/CD (no `paths:` filter needed — every push deploys)
- The intel repo can be kept private independently of the main app

## Options Considered

### Option A: Monorepo Subfolder

- Intel stays at `docs/infrastructure/intel/`
- GitHub Actions uses `paths:` filter

**Pros**: Single PR for coordinated NextJS + Intel changes  
**Cons**: CI path filtering complexity, monorepo grows, Python in a JS repo

### Option B: Separate Repository (Selected)

- Intel lives at `https://github.com/t0ttora/intel`
- Every push to `main` triggers deploy
- App code is at repo root — no path extraction needed

**Pros**: Clean separation, simple CI, independent versioning  
**Cons**: Cross-repo coordination requires two PRs for tightly coupled changes

## Decision

**Option B: Separate repository at `t0ttora/intel`.**

The intel repo is the deployment unit. `setup-vps.sh` is called with `INTEL_PATH=.` since the code lives at root. GitHub Actions deploys on every push to `main` — no path filter needed.

## Consequences

- GitHub Actions workflow in `t0ttora/intel` repo deploys on every push to `main`
- `setup-vps.sh` prompt: GitHub repo = `https://github.com/t0ttora/intel.git`, path = `.`
- NobleVerse monorepo keeps a copy of docs at `docs/infrastructure/intel/docs/` for cross-reference
- The `.env`, `.venv`, `backup.sh`, and `update.sh` are excluded from rsync to preserve VPS-specific state

## Review Trigger

Re-evaluate if Intel needs to import shared types from the NextJS codebase directly.
