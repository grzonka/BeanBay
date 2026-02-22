# Project State: BeanBay

**Last updated:** 2026-02-22
**Current phase:** Phase 12 — Manual Brew Input (complete) ✅

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-22)

**Core value:** Every coffee brew teaches the system something — the app must make it effortless to capture that feedback from a phone at the espresso machine and return increasingly better recommendations.
**Current focus:** v0.1.1 — UX Polish & Manual Brew ✅ SHIPPED

## Milestone History

| Milestone | Phases | Plans | Status | Date |
|-----------|--------|-------|--------|------|
| v1 MVP | 1-6 | 16 | ✅ Shipped | 2026-02-22 |
| v0.1.0 Release & Deploy | 7-9 | 5 | ✅ Shipped | 2026-02-22 |
| v0.1.1 UX Polish & Manual Brew | 10-12 | 11 | ✅ Shipped | 2026-02-22 |

## Current Position

Phase: 12 of 12 (Manual Brew Input) — Plan 4 of 4 complete
Plan: 4 of 4 — 12-04 complete
Status: ✅ Phase 12 complete — v0.1.1 milestone complete
Last activity: 2026-02-22 — Completed 12-04-PLAN.md (adaptive range extension, 4 new tests, 130 total)

Progress: [████████████████████████████████████████████] 100% (32 plans complete)

## Performance Metrics

**Velocity:**
  - Total plans completed: 32 (v1: 16, v0.1.0: 5, v0.1.1: 11)
  - v0.1.1 plans completed: 11 (phase 10: 2, phase 11: 2, phase 12: 4+1 quick task)
  - v0.1.1 total plans: 11

## Accumulated Context

### Key Technical Decisions
See: .planning/PROJECT.md (Key Decisions table)

| Phase | Decision | Rationale |
|-------|----------|-----------|
| 11 | Render /brew with no_active_bean flag instead of redirect | Silent redirects are confusing on mobile; inline prompt keeps user in context |
| 11 | Other brew routes still redirect when no bean | POST /recommend, GET /best, POST /record genuinely require a bean to function |
| 11 | data-touched attribute on taste slider (not JS var) | State co-located with DOM element; easier to reset via toggleFailed; easier to inspect |
| 11 | Display "—" as initial taste slider label | 7.0 default looked like a deliberate choice; "—" clearly signals unset |
| 12 | Add POST /beans/set-active for bean picker form | Existing activate route uses path param; form <select> submits body field |
| 12 | Bounds validation only for is_manual == "true" | Optimizer recs always in-bounds; manual entries need validation |
| 12 | name attribute on number inputs (not sliders) | Sliders are for UX sync only; numbers carry submitted value with correct precision |
| 12 | window.toggleFailed exposed from tags.js IIFE | Three templates needed same function; single source of truth avoids drift |
| 12 | hidden(no) + checkbox(yes) for saturation | HTML checkbox submits nothing when unchecked; hidden ensures saturation=no always present |
| 12 | Delete checkbox uses form attribute (not nested) | Checkbox inside shot card, outside delete form; HTML form= attribute links it regardless of DOM nesting |
| 12 | Capture shot IDs before delete in tests | SQLAlchemy raises ObjectDeletedError accessing deleted instance attrs after expire_all() |
| 12 | Remove min/max from number inputs; use data-min/data-max | Lets users type out-of-range values to trigger range extension flow |
| 12 | fetch extend-ranges then form.submit() | Ensures bounds update persists before /brew/record validates; no page reload needed |

### Branding
- **Name:** BeanBay | **Domain:** beanbay.coffee
- **Docker:** ghcr.io/grzonka/beanbay | **Release:** v0.1.0 live

### Quick Tasks Completed

| ID | Task | Date |
|----|------|------|
| 001 | Fix CI test DB isolation | 2026-02-22 |

## Session Continuity

### Last Session
- **Date:** 2026-02-22
- **What happened:** Executed 12-04-PLAN.md — POST /brew/extend-ranges endpoint updates Bean.parameter_overrides; client-side out-of-range detection on manual form with confirm() prompt + fetch before submit; data-min/data-max/data-param on number inputs; 4 new tests (130 total). Phase 12 complete, v0.1.1 milestone shipped.
- **Where we left off:** All phases complete. v0.1.1 done.

### Next Steps
No planned next steps. v0.1.1 is complete. Start a new milestone planning session when ready for v0.1.2.

---
*State initialized: 2026-02-21*
*Last updated: 2026-02-22 after completing 12-04 adaptive range extension — v0.1.1 SHIPPED*
