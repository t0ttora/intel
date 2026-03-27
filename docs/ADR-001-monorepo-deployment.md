# ADR-001: Deploy Intel from Monorepo Subfolder

**Status**: Accepted  
**Date**: 2026-03-27  
**Deciders**: Engineering team

## Context

Noble Intel is a Python FastAPI service that runs on a dedicated VPS. The code currently lives at `docs/infrastructure/intel/` inside the main NobleVerse monorepo. We need to decide how to manage and deploy it.

## Decision Drivers

- Minimize operational complexity
- Enable automatic deployment on code changes
- Keep code discoverable (intel docs + NextJS integration in one place)
- Avoid maintaining a separate repo/CI pipeline until team/complexity warrants it

## Options Considered

### Option A: Separate Git Repository

- Intel gets its own repo (e.g. `nobleverse/noble-intel`)
- Separate CI/CD pipeline
- Independent release cycle

**Pros**: Clean separation, independent versioning  
**Cons**: Split context, two repos to maintain, separate PR process, harder to coordinate NextJS + Intel changes

### Option B: Monorepo Subfolder (Selected)

- Intel stays at `docs/infrastructure/intel/`
- GitHub Actions uses `paths:` filter to trigger deploy only on Intel changes
- `setup-vps.sh` already supports `INTEL_PATH` parameter for subfolder extraction

**Pros**: Single repo, single PR for coordinated changes, no extra infrastructure  
**Cons**: CI workflow needs path filter, monorepo grows in size

## Decision

**Option B: Monorepo subfolder.**

The `setup-vps.sh` script and `update.sh` already handle subfolder extraction via `rsync`. The GitHub Actions `paths:` filter ensures deploys only trigger on Intel changes. No infrastructure changes needed.

## Consequences

- GitHub Actions workflow uses `paths: ['docs/infrastructure/intel/**']` to scope deploys
- Code changes to Intel and NextJS can be coordinated in a single PR
- If Intel grows to need its own team or release cycle, extract to a separate repo at that point
- The `.env`, `.venv`, `backup.sh`, and `update.sh` are excluded from rsync to preserve VPS-specific state

## Review Trigger

Re-evaluate this decision when:
- Intel has more than 2 regular contributors
- Intel needs independent release versioning
- Monorepo CI times become problematic due to Intel changes
