# Milestone v1: BrewFlow MVP

**Status:** SHIPPED 2026-02-22
**Phases:** 1-6
**Total Plans:** 16

## Overview

Phone-first espresso optimization app using Bayesian optimization (BayBE). From zero to fully working app with bean management, recipe optimization, shot history, insights visualization, and analytics — all deployable as a single Docker container on an Unraid homeserver.

## Phases

### Phase 1: Foundation & Infrastructure

**Goal:** The project has a working skeleton — database, BayBE integration layer, and Docker container — deployable on the Unraid server and accessible from any device on the network.
**Depends on:** None
**Plans:** 3 plans

Plans:
- [x] 01-01-PLAN.md — Project scaffolding, config, SQLAlchemy models, Alembic migrations
- [x] 01-02-PLAN.md — BayBE optimizer service layer (hybrid campaigns, thread-safe)
- [x] 01-03-PLAN.md — FastAPI app skeleton, Docker deployment, comprehensive tests

**Requirements:** INFRA-02, INFRA-03

**Details:**
- SQLite database with Bean and Measurement models (UUID primary keys)
- BayBE OptimizerService with hybrid search space (5 continuous + 1 categorical parameter)
- Campaign files ~7.5KB (down from 20MB with discrete approach)
- Thread-safe optimizer with asyncio.to_thread for non-blocking recommendations
- Dockerfile (multi-stage, CPU-only PyTorch) + docker-compose.yml
- 12 tests at completion

---

### Phase 2: Bean Management & Mobile Shell

**Goal:** Users can manage their coffee beans from their phone — create beans, select one for optimization, and see their collection — with a mobile-first layout that works with messy hands.
**Depends on:** Phase 1
**Plans:** 2 plans

Plans:
- [x] 02-01-PLAN.md — Bean CRUD routes, templates, mobile-first CSS
- [x] 02-02-PLAN.md — Bean selection, parameter overrides, mobile polish

**Requirements:** BEAN-01, BEAN-02, BEAN-03, INFRA-01

**Details:**
- Bean CRUD with htmx-powered UI
- Active bean via httpOnly cookie (single-user, no auth)
- Dark espresso theme with 48px+ touch targets
- Per-bean parameter overrides with fingerprint-based campaign invalidation
- 23 bean tests at completion

---

### Phase 3: Optimization Loop

**Goal:** Users can run the complete espresso optimization cycle from their phone — get a recommendation, brew, rate the shot (or mark it failed), and recall the best recipe to re-brew.
**Depends on:** Phase 2
**Plans:** 2 plans

Plans:
- [x] 03-01-PLAN.md — Brew router, optimization loop (recommend, record, repeat best)
- [x] 03-02-PLAN.md — Gap closure: fix Repeat Best dedup, add bean deactivate UI

**Requirements:** OPT-01, OPT-02, OPT-03, OPT-04, OPT-05, OPT-06, SHOT-03

**Details:**
- 5 brew endpoints: index, recommend, record, best, best-record
- Server-side pending_recommendations dict for single-user session state
- Deduplication via unique recommendation_id on Measurement table
- Failed shots auto-set taste=1 in router before DB write
- Fresh UUID per /brew/best visit (page-visit scoped dedup)
- Bean deactivation endpoint and UI
- 19 brew tests + 7 optimizer tests

---

### Phase 4: Shot History & Feedback Depth

**Goal:** Users can review their brewing history for any bean and optionally capture richer feedback (flavor dimensions, notes) for shots they want to analyze more deeply.
**Depends on:** Phase 3
**Plans:** 3 plans

Plans:
- [x] 04-01-PLAN.md — Schema + feedback panel (notes, flavor sliders, tags) on brew forms
- [x] 04-02-PLAN.md — History list page with filtering by bean and taste score
- [x] 04-03-PLAN.md — Shot detail modal + retroactive editing

**Requirements:** SHOT-01, SHOT-02, VIZ-03

**Details:**
- Collapsible feedback panel with notes, 6 flavor sliders, tag input
- flavor_tags as JSON-encoded String column (SQLite compatibility)
- Untouched slider null semantics (removeAttribute('name') on submit)
- History page with htmx-powered filtering by bean and minimum taste
- Shot detail modal via HX-Trigger + dialog.showModal()
- Retroactive edit with hx-swap-oob for in-place row updates
- 19 history tests at completion

---

### Phase 5: Insights & Trust

**Goal:** Users can see that the optimizer is learning and understand why it suggests what it suggests — building confidence to keep experimenting.
**Depends on:** Phase 3, Phase 4
**Plans:** 3 plans

Plans:
- [x] 05-01-PLAN.md — Recommendation explanation (explore/exploit label + predicted taste range)
- [x] 05-02-PLAN.md — Insights page with progress chart (Chart.js) + convergence indicator
- [x] 05-03-PLAN.md — Gap closure: fix recommend crash + improve phase badge accuracy

**Requirements:** VIZ-01, VIZ-02, VIZ-05

**Details:**
- get_recommendation_insights() with TwoPhaseMetaRecommender phase detection
- campaign.posterior_stats() for predicted taste range
- Chart.js progress chart (cumulative best line + shot scatter)
- 5-state convergence badge (rule-based heuristic)
- campaign.clear_cache() fix for 2nd+ recommend crash
- switch_after=5 for meaningful random exploration
- Three-phase badge: random (0-4) / bayesian_early (5-7) / bayesian (8+)
- 21 optimizer tests at completion

---

### Phase 6: Analytics & Exploration

**Goal:** Users with accumulated data across multiple beans can compare recipes, explore parameter relationships, and see their overall brewing statistics.
**Depends on:** Phase 4, Phase 5
**Plans:** 2 plans

Plans:
- [x] 06-01-PLAN.md — Analytics page with brew statistics + cross-bean recipe comparison
- [x] 06-02-PLAN.md — Parameter exploration heatmap on insights page

**Requirements:** VIZ-04, ANLYT-01, ANLYT-02

**Details:**
- Analytics page with 6-metric stats card (total shots, avg taste, personal best, improvement rate)
- Cross-bean best recipe comparison (vertical card layout, mobile-friendly)
- Chart.js scatter heatmap (grind x temperature, colored by taste)
- Failed shots as grey crossRot markers (accessible distinction)
- 3-shot minimum threshold for meaningful heatmap
- 5 analytics + 15 insights tests at completion

---

## Phase Dependencies

```
Phase 1: Foundation & Infrastructure
  -> Phase 2: Bean Management & Mobile Shell
       -> Phase 3: Optimization Loop
            +-> Phase 4: Shot History & Feedback Depth
            |    +-> Phase 5: Insights & Trust (also depends on Phase 3)
            |    +-> Phase 6: Analytics & Exploration (also depends on Phase 5)
            +-> Phase 5: Insights & Trust
                 +-> Phase 6: Analytics & Exploration
```

**Critical path:** Phase 1 -> Phase 2 -> Phase 3 -> Phase 4 -> Phase 5 -> Phase 6

## Milestone Summary

**Key Decisions:**
- Hybrid BayBE parameters: 5 continuous + 1 categorical (7.5KB campaigns vs 20MB discrete)
- FastAPI + Jinja2/htmx + SQLite + Chart.js stack (server-rendered, no SPA)
- Active bean via httpOnly cookie (single-user home app, no auth)
- Per-bean parameter overrides with fingerprint-based campaign invalidation
- Measurements-as-source-of-truth pattern (campaigns are rebuildable)
- CPU-only PyTorch to save ~1GB in Docker image
- Server-side pending_recommendations dict for session state
- campaign.clear_cache() before recommend() to prevent BayBE crash
- Three-phase optimizer badges: random / bayesian_early / bayesian

**Issues Resolved:**
- BayBE discrete vs hybrid parameter space (resolved: hybrid, 7.5KB files)
- Repeat Best deduplication too aggressive (resolved: fresh UUID per page visit)
- 2nd+ recommend crash (resolved: campaign.clear_cache() call)
- Phase badge inaccuracy (resolved: switch_after=5, three-phase labeling)
- Analytics improvement_rate test flake (resolved: 20 shots needed, not 10)

**Issues Deferred:**
- Docker build not verified in dev environment (no daemon — deferred to Unraid deployment)
- Manual brew input feature (backlog item, not v1 requirement)

**Technical Debt Incurred:**
- Duplicated _get_active_bean helper in brew.py and insights.py
- Dead app/routes/ directory with empty __init__.py
- In-memory pending_recommendations lost on server restart
- Startup ALTER TABLE migration outside Alembic
- Silent ValueError on override parsing (no user feedback)

---

*Archived: 2026-02-22 as part of v1 milestone completion*
*For current project status, see .planning/PROJECT.md*
