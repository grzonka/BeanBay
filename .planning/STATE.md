# Project State: BeanBay

**Last updated:** 2026-02-22
**Current phase:** v1.1 milestone planned. Ready to plan Phase 7.

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
| 7 | Rebrand & Cleanup | Not started |
| 8 | Documentation & Release | Not started |
| 9 | Deployment Templates | Not started |

**Overall progress:** v1.1 roadmap and requirements created. Phase plans needed.

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
- **What happened:** Completed v1 milestone archival. Started v1.1 planning. Chose BeanBay as new name (beanbay.coffee domain secured). Created v1.1 REQUIREMENTS.md (16 requirements) and ROADMAP.md (3 phases: 7-9). Discussed v2 vision extensively (multi-method brewing, grinder management, water tracking, Beanconqueror import, cross-brew intelligence).
- **Where we left off:** v1.1 roadmap created. Need to plan Phase 7 (Rebrand & Cleanup) next.

### Next Steps
1. Create GitHub repo `grzonka/beanbay` and add remote
2. Plan Phase 7 — `/gsd-plan-phase 7`
3. Execute phases 7-9
4. Deploy to Unraid
5. Plan v2 milestone

---
*State initialized: 2026-02-21*
*Last updated: 2026-02-22*
