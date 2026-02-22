# Project State: BeanBay

**Last updated:** 2026-02-22
**Current phase:** Phase 8 — Documentation & Release (in progress).

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-22)

**Core value:** Every coffee brew teaches the system something — the app must make it effortless to capture that feedback from a phone at the espresso machine and return increasingly better recommendations.
**Current focus:** v0.1.0 — Rebrand to BeanBay, clean up, ship, deploy.

## Milestone History

| Milestone | Phases | Plans | Status | Date |
|-----------|--------|-------|--------|------|
| v1 MVP | 1-6 | 16 | Shipped | 2026-02-22 |
| v0.1.0 Release & Deploy | 7-9 | 5 | In Progress | 2026-02-22 |

See: .planning/MILESTONES.md

## Phase Status

### v0.1.0 Phases

| Phase | Name | Status |
|-------|------|--------|
| 7 | Rebrand & Cleanup | ✅ Complete & Verified |
| 8 | Documentation & Release | 🔄 In Progress (1/2 plans done) |
| 9 | Deployment Templates | Not started |

**Overall progress:** Phase 8 in progress. 3/5 v0.1.0 plans done.

## Current Position

Phase: 8 of 9 (Documentation & Release) — In Progress
Plan: 1 of 2 in Phase 8
Status: In progress
Last activity: 2026-02-22 - Completed 08-01-PLAN.md (README.md created)

Progress: ███░░ 60% (3/5 v0.1.0 plans)

## Blockers

- ~~GitHub repo not yet created.~~ ✅ `grzonka/beanbay` exists on GitHub.
- Docker build not verified (daemon not available in dev environment).

## Accumulated Context

### Key Technical Decisions
See: .planning/PROJECT.md (Key Decisions table)

### Backlog
- **Manual brew input** — User can manually enter all 6 recipe parameters and submit a taste score, bypassing BayBE recommendation. Manual entries fed to BayBE via add_measurement. Deferred to v2.

### Tech Debt (from v1 audit — RESOLVED in Phase 7)
- ✅ Duplicated _get_active_bean helper in brew.py and insights.py
- ✅ Dead app/routes/ directory with empty __init__.py
- ✅ In-memory pending_recommendations dict lost on server restart
- ✅ Startup ALTER TABLE migration outside Alembic
- ✅ Silent ValueError on override parsing
See: .planning/phases/07-rebrand-cleanup/07-02-SUMMARY.md

### Branding
- **New name:** BeanBay (was BrewFlow)
- **Domain:** beanbay.coffee
- **Repo:** grzonka/beanbay (to be created)
- **Docker image:** ghcr.io/grzonka/beanbay

## Session Continuity

### Last Session
- **Date:** 2026-02-22
- **What happened:** Executed Phase 8 Plan 01. Created README.md with WIP indication, Docker quick start, dev setup, and Apache 2.0 license reference. 57 lines, concise and honest.
- **Where we left off:** Phase 8 in progress. 1/2 plans done. Ready for 08-02 (GitHub Actions CI/CD + v0.1.0 release).

### Next Steps
1. Execute 08-02 — GitHub Actions CI/CD workflows (test + Docker publish) + v0.1.0 release
2. Execute 09-01 — Docker files update + Unraid CA XML template
3. Deploy to Unraid

---
*State initialized: 2026-02-21*
*Last updated: 2026-02-22 after 08-01 (README)*
