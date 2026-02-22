# Project State: BeanBay

**Last updated:** 2026-02-22
**Current phase:** Phase 7 — Rebrand & Cleanup (in progress)

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-22)

**Core value:** Every coffee brew teaches the system something — the app must make it effortless to capture that feedback from a phone at the espresso machine and return increasingly better recommendations.
**Current focus:** v1.1 — Rebrand to BeanBay, clean up, ship, deploy.

## Milestone History

| Milestone | Phases | Plans | Status | Date |
|-----------|--------|-------|--------|------|
| v1 MVP | 1-6 | 16 | Shipped | 2026-02-22 |
| v1.1 Release & Deploy | 7-9 | TBD | Planning | 2026-02-22 |

See: .planning/MILESTONES.md

## Phase Status

### v1.1 Phases

| Phase | Name | Status |
|-------|------|--------|
| 7 | Rebrand & Cleanup | In progress (1/2 plans complete) |
| 8 | Documentation & Release | Not started |
| 9 | Deployment Templates | Not started |

**Overall progress:** 07-01 complete. 1/5 v1.1 plans done.

## Current Position

Phase: 7 of 9 (Rebrand & Cleanup)
Plan: 1 of 2 in current phase
Status: In progress
Last activity: 2026-02-22 - Completed 07-01-PLAN.md

Progress: ░░░░░ 20% (1/5 v1.1 plans)

## Blockers

- **GitHub repo not yet created.** User needs to create `grzonka/beanbay` on GitHub and add remote before Phase 8 (CI/release).
- Docker build not verified (daemon not available in dev environment).

## Accumulated Context

### Key Technical Decisions
See: .planning/PROJECT.md (Key Decisions table)

### Backlog
- **Manual brew input** — User can manually enter all 6 recipe parameters and submit a taste score, bypassing BayBE recommendation. Manual entries fed to BayBE via add_measurement. Deferred to v2.

### Tech Debt (from v1 audit — to be fixed in Phase 7)
- Duplicated _get_active_bean helper in brew.py and insights.py
- Dead app/routes/ directory with empty __init__.py
- In-memory pending_recommendations dict lost on server restart
- Startup ALTER TABLE migration outside Alembic
- Silent ValueError on override parsing
See: .planning/milestones/v1-MILESTONE-AUDIT.md

### Branding
- **New name:** BeanBay (was BrewFlow)
- **Domain:** beanbay.coffee
- **Repo:** grzonka/beanbay (to be created)
- **Docker image:** ghcr.io/grzonka/beanbay

## Session Continuity

### Last Session
- **Date:** 2026-02-22
- **What happened:** Executed 07-01-PLAN.md. Renamed all BrewFlow references to BeanBay across Python source files, HTML templates, static assets, and test assertions. All 108 tests pass.
- **Where we left off:** 07-01 complete. Ready for 07-02 (tech debt cleanup).

### Next Steps
1. Execute 07-02-PLAN.md — fix all 5 tech debt items
2. Execute phases 8-9
3. Create GitHub repo `grzonka/beanbay` (needed before Phase 8)
4. Deploy to Unraid

---
*State initialized: 2026-02-21*
*Last updated: 2026-02-22*
