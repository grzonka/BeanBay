# BeanBay

## What This Is

A phone-first web application for optimizing coffee recipes using Bayesian optimization (BayBE). Runs on a homeserver (Unraid/Docker) or any machine with Docker, letting the user dial in any coffee bean by iterating: get a recommendation, brew, taste, rate, repeat. BayBE learns from each shot to suggest better recipes over time.

Built with FastAPI + Jinja2/htmx + SQLite + Chart.js. Deployed as a single Docker container.

**Website:** beanbay.coffee

## Core Value

Every coffee brew teaches the system something — the app must make it effortless to capture that feedback from a phone at the espresso machine and return increasingly better recommendations.

## Current State

**Shipped:** v1 MVP, v0.1.0, v0.1.1 (all 2026-02-22)
**Active milestone:** v0.2.0 — Multi-method brewing, equipment management, transfer learning
**Codebase:** ~8,295 LOC (Python, HTML, CSS/JS), 130 tests passing
**Stack:** FastAPI, Jinja2/htmx, SQLite, Chart.js, BayBE, Docker

## Requirements

### Validated

- ✓ Manage coffee beans (create, select, view per-bean history) — v1
- ✓ Get BayBE-powered recipe recommendations with transparent reasoning (why this suggestion, exploration vs exploitation) — v1
- ✓ Quick feedback flow: taste score (1-10) with optional expandable flavor profile (acidity, sweetness, body, bitterness, aroma, intensity) and notes — v1
- ✓ Shot failure tracking (choked/gusher auto-sets taste to 1) — v1
- ✓ Optimization progress visualization (cumulative best over time per bean) — v1
- ✓ Parameter exploration charts (heatmaps/scatter of grind, temp vs taste) — v1
- ✓ Cross-bean comparison (best recipes side by side) — v1
- ✓ Brew statistics dashboard (total shots, averages, personal records) — v1
- ✓ Mobile-first responsive UI that works well with messy hands — v1
- ✓ Docker deployment for homeserver — v1
- ✓ Accessible from anywhere on the local network — v1
- ✓ Mobile hamburger/drawer navigation, desktop sidebar layout — v0.1.1
- ✓ Active bean indicator displays cleanly without overflow in all viewports — v0.1.1
- ✓ Taste score slider starts inactive and must be touched before submission — v0.1.1
- ✓ Failed shot toggle preserves override behavior with new inactive pattern — v0.1.1
- ✓ No-bean prompt on /brew with direct link to bean selection — v0.1.1
- ✓ Manual brew input with all 6 parameters + taste score — v0.1.1
- ✓ Manual brews feed into BayBE optimization via add_measurement — v0.1.1
- ✓ Manual brews visually distinguishable in shot history (blue badge) — v0.1.1

### Active (v0.2.0)

- **Multi-method brewing** — Support espresso, pour-over (V60 etc.), and other methods. Each method has its own parameter set (e.g., V60 adds bloom). Users configure brewer + paper + water + bean combinations.
- **Equipment management** — Users create equipment items (grinders, brewers/machines, papers, water recipes) and assemble them into "brew setups." Equipment is context for optimization, not a BayBE variable. A campaign = bean + method + equipment combo.
- **Grinder management** — Support multiple grinders with different dial types (stepped vs stepless). Grind setting is specific to the grinder context.
- **Water tracking** — Named water recipes (e.g., "Volvic", "Third Wave Water") with optional mineral composition and notes for how it was made.
- **Enhanced bean metadata** — Roast date, origin, process, variety (all optional). A "coffee" can have multiple bags (buying the same coffee twice). Optional cost per bag.
- **Cross-brew intelligence via BayBE transfer learning** — When starting a new bean with known properties (process + variety), seed BayBE's first recommendation using transfer learning (TaskParameter) from history of similar beans, rather than random exploration.

### Out of Scope (current milestone)

- Multi-user accounts — v3 vision
- Community/shared database — v3
- Beanconqueror import — backlog (deferred from v0.2)

## Context

- **Shipped v1:** 6 phases, 16 plans, 108 tests, ~7,632 LOC across Python/HTML/CSS/JS
- **Shipped v0.1.0:** 3 phases, 5 plans. Rebrand, CI/CD, Docker image, Unraid template.
- **Shipped v0.1.1:** 3 phases, 8 plans, 130 tests, ~8,295 LOC. Responsive nav, taste UX, manual brew.
- **v0.2.0 scope:** Multi-method brewing, equipment management (grinders, brewers, papers, water), enhanced bean metadata (bags, process, variety), cross-brew transfer learning via BayBE TaskParameter.
- **Hardware setup:** Sage Dual Boiler (Slayer mod) + DF83v grinder. Parameters tuned to this specific machine's ranges.
- **BayBE:** Hybrid search space (5 continuous + 1 categorical), ~7.5KB campaign files. Three-phase optimization: random (0-4 shots) -> Learning (5-7) -> Bayesian optimization (8+).
- **Usage pattern:** Primarily phone at the espresso machine. Quick interactions most days, occasional deep tasting sessions on laptop.
- **Deployment:** Unraid server via Docker. Single container, SQLite + BayBE JSON campaign files in persistent volume. Also available to any Docker user.
- **Known tech debt:** v1 tech debt resolved in Phase 7. v0.1.1 incurred 3 minor cosmetic items (orphaned CSS rules, inline styles in drawer, undefined --text-xs var). See milestones/v0.1.1-MILESTONE-AUDIT.md.

## Constraints

- **Backend language**: Python — BayBE is a Python library, no way around it
- **Optimization engine**: BayBE — already proven, campaign state is JSON-serializable
- **Parameters**: Configurable per brew method — espresso has 6 params (current), pour-over has its own set. Grind setting is grinder-specific.
- **Single user**: Personal use only, no auth needed
- **Self-hosted**: Must run on local server via Docker (Unraid or any Docker host)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Migrate away from Marimo | Marimo requires laptop, no phone support, no remote access | ✓ Good — full webapp shipped |
| Start fresh (no data migration) | Existing data is limited, clean start preferred | ✓ Good — clean schema design |
| Phone-first UI design | Primary usage is at the espresso machine with phone | ✓ Good — dark theme, 48px+ targets |
| Quick + expandable feedback | Fast taste score by default, optional flavor breakdown for deep sessions | ✓ Good — collapsible panel pattern |
| Docker deployment on Unraid | Matches existing homeserver infrastructure | ✓ Good — single container ready |
| Transparent recommendations | Show why BayBE suggests a recipe (exploration vs exploitation, uncertainty) | ✓ Good — 3-phase badges + predicted taste |
| FastAPI + Jinja2/htmx stack | Server-rendered, no SPA complexity, htmx for dynamic updates | ✓ Good — simple, fast, low overhead |
| Hybrid BayBE parameters | 5 continuous + 1 categorical vs all-discrete | ✓ Good — 7.5KB vs 20MB campaign files |
| SQLite as database | Single-user, embedded, no separate DB server | ✓ Good — zero ops overhead |
| Chart.js for visualization | CDN-loaded, no build step, rich chart types | ✓ Good — progress charts + heatmaps working |
| Measurements as source of truth | Campaigns rebuildable from measurement data | ✓ Good — disaster recovery works |
| Rebrand to BeanBay | Better name — "bean" first, "bay" as gathering place + Bayesian hint | ✓ Good — v0.1.0 shipped |
| Hamburger/drawer on mobile | Tab row overflowed with many nav items + long bean name | ✓ Good — clean on all screen sizes |
| Desktop sidebar layout | Centered 480px column wasted widescreen space | ✓ Good — full-width usage |
| Inactive taste slider (data-touched) | Default 7.0 encouraged lazy submissions; "---" label signals unset | ✓ Good — deliberate scoring |
| Inline no-bean prompt | Silent redirect confusing on mobile; keeps user in context | ✓ Good — clear guidance |
| Manual brew with BayBE integration | Users need to record brews outside recommendation flow | ✓ Good — feeds optimization |
| Adaptive parameter ranges | Manual brews may exceed default ranges; confirm + extend | ✓ Good — flexible without breaking optimizer |
| Equipment as context (v0.2) | Equipment defines experiment context; BayBE optimizes recipe variables within that context | Decided — comparison between setups at analytics level |
| Transfer learning via TaskParameter (v0.2) | BayBE TaskParameter enables cross-bean cold-start seeding from similar beans | Validated — feasible with matching search spaces |
| Bean bags model (v0.2) | A "coffee" can have multiple bags; same coffee bought twice shares identity | Decided — supports transfer learning similarity matching |

---
*Last updated: 2026-02-22 after v0.2.0 milestone kickoff*
