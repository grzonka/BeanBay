# Project State: BeanBay

**Last updated:** 2026-02-23
**Current phase:** Phase 16 — Cross-Brew Transfer Learning ✅ COMPLETE

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
| v0.2.0 Multi-Method & Intelligence | 13-16 | 11 | ✅ Shipped | 2026-02-23 |

## Current Position

Phase: 16 of 16 (Cross-Brew Transfer Learning) — ✅ Complete
Plan: 2 of 2 complete
Status: Phase 16 complete — v0.2.0 feature-complete
Last activity: 2026-02-23 — Completed 16-02-PLAN.md (transfer learning wire-up, 240 tests)

Progress: [████████████████████████████████████████████] 100% (13/13 v0.2.0 plans)

## Performance Metrics

**Velocity:**
  - Total plans completed: 41 (v1: 16, v0.1.0: 5, v0.1.1: 8, v0.2.0: 12)
  - Total phases completed: 16 complete
  - All milestones shipped same day (Feb 22-23, 2026)

## Accumulated Context

### Key Technical Decisions
See: .planning/PROJECT.md (Key Decisions table — 22+ decisions tracked)

### Branding
- **Name:** BeanBay | **Domain:** beanbay.coffee
- **Docker:** ghcr.io/grzonka/beanbay | **Latest release:** v0.2.0

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

### Phase 16 Key Decisions
- **Transfer metadata as .transfer sidecar file:** Consistent with .bounds sidecar pattern; easy presence-check without loading campaign
- **transfer_metadata stored in pending recommendation dict:** Survives server restarts; show_recommendation reads metadata without extra optimizer call
- **TYPE_CHECKING guard for Bean/Session imports in optimizer.py:** Avoids circular import at module load time; type hints only, not runtime
- **None return when no training data:** Even with matching similar_beans, if no actual DB measurements exist for those beans, returns None gracefully

### Quick Tasks Completed

| ID | Task | Date |
|----|------|------|
| 001 | Fix CI test DB isolation | 2026-02-22 |

## Session Continuity

### Last Session
- **Date:** 2026-02-23
- **What happened:** Executed Phase 16 (2/2 plans). SimilarityService, TransferLearningService, full optimizer wire-up, router integration, template badge. 240/240 tests passing.
- **Where we left off:** Phase 16 complete. v0.2.0 feature-complete.

### Next Steps
1. ✅ Tag v0.2.0 release — done (2026-02-23)
2. ✅ Docker image published — ghcr.io/grzonka/beanbay:v0.2.0 (CI triggered by tag push)
3. Plan next milestone (backlog)

---
*State initialized: 2026-02-21*
*Last updated: 2026-02-23 — Phase 16 complete (2/2 plans, transfer learning fully wired, 240 tests)*
