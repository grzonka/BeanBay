# Project State: BeanBay

**Last updated:** 2026-02-23
**Current phase:** Phase 15 — Multi-Method Brewing ✅ COMPLETE

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-22)

**Core value:** Every coffee brew teaches the system something — the app must make it effortless to capture that feedback from a phone at the espresso machine and return increasingly better recommendations.
**Current focus:** v0.2.0 — Multi-method brewing, equipment management, transfer learning

## Milestone History

| Milestone | Phases | Plans | Status | Date |
|-----------|--------|-------|--------|------|
| v1 MVP | 1-6 | 16 | ✅ Shipped | 2026-02-22 |
| v0.1.0 Release & Deploy | 7-9 | 5 | ✅ Shipped | 2026-02-22 |
| v0.1.1 UX Polish & Manual Brew | 10-12 | 8 | ✅ Shipped | 2026-02-22 |
| v0.2.0 Multi-Method & Intelligence | 13+ | TBD | 🔄 Planning | 2026-02-22 |

## Current Position

Phase: 15 of 16 (Multi-Method Brewing) — ✅ Complete
Plan: 3 of 3 complete
Status: Phase complete — ready for Phase 16
Last activity: 2026-02-23 — Completed 15-03-PLAN.md (multi-method tests + setup context badge in history, 210 tests)

Progress: [███████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 73% (11/15 v0.2.0 plans est.)

## Performance Metrics

**Velocity:**
  - Total plans completed: 38 (v1: 16, v0.1.0: 5, v0.1.1: 8, v0.2.0: 9)
  - Total phases completed: 15 complete, 16 pending
  - All milestones shipped same day (Feb 22, 2026)

## Accumulated Context

### Key Technical Decisions
See: .planning/PROJECT.md (Key Decisions table — 22 decisions tracked)

### Branding
- **Name:** BeanBay | **Domain:** beanbay.coffee
- **Docker:** ghcr.io/grzonka/beanbay | **Latest release:** v0.1.1

### v0.2.0 Key Design Decisions (from questioning phase)
- **Equipment as context:** Equipment defines the experiment context; BayBE optimizes recipe variables within that context. Comparison between equipment setups happens at analytics level, not optimizer level.
- **Transfer learning via TaskParameter:** BayBE's TaskParameter class enables cross-bean cold-start. Similar beans (by process + variety) provide training data; new bean is the test task. Search spaces must match for transfer learning to work.
- **Bean bags model:** A "coffee" can have multiple bags. Same coffee bought twice shares identity, enabling richer history and transfer learning similarity matching.
- **Beanconqueror import deferred:** Moved to backlog, not in v0.2 scope.

### Phase 14 Key Decisions
- **Retire-only pattern (no deletion):** Preserves history; retired equipment hidden by default, shown with toggle
- **Cascade retire, manual restore:** Retiring a component auto-retires all setups using it; restoring does NOT cascade
- **active_setup_id cookie:** Same pattern as active_bean_id; 1-year expiry; cleared if setup is retired
- **Setup is context for brew page:** Brew action buttons require a bean but setup is optional (for future BayBE integration)

### Phase 15 Key Decisions
- **Campaign key format `bean__method__setup`:** Double-underscore separator avoids collisions with bean IDs that may contain underscores
- **Pour-over param set:** Adds `preinfusion_pct`, `target_yield`, `saturation` (all continuous, ranges tuned for V60-style brewing)
- **Legacy migration at startup:** `migrate_legacy_campaigns()` runs in `main.py` lifespan, transparently maps old `{bean_id}` keys to `{bean_id}__espresso__None`
- **brew_setup_name in shot dict:** Template has no ORM access, so `brew_setup_name` added as plain key to shot dicts in `_build_shot_dicts()` (not ORM relationship access)

### Quick Tasks Completed

| ID | Task | Date |
|----|------|------|
| 001 | Fix CI test DB isolation | 2026-02-22 |

## Session Continuity

### Last Session
- **Date:** 2026-02-23
- **What happened:** Executed Phase 15 (3/3 plans). Campaign key scoped to bean+method+setup, pour-over param set, brew_setup_id recorded on Measurement, setup context badge in history. 210/210 tests passing.
- **Where we left off:** Phase 15 complete (3/3 plans done). Ready for Phase 16.

### Next Steps
1. Plan Phase 16 (Cross-Brew Transfer Learning)
2. Execute Phase 16 plans

---
*State initialized: 2026-02-21*
*Last updated: 2026-02-23 — Phase 15 complete (3/3 plans, campaign_key by bean+method+setup, pour-over params, 210 tests)*
