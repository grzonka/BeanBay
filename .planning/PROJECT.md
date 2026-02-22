# BeanBay

## What This Is

A phone-first web application for optimizing coffee recipes using Bayesian optimization (BayBE). Runs on a homeserver (Unraid/Docker) or any machine with Docker, letting the user dial in any coffee bean by iterating: get a recommendation, brew, taste, rate, repeat. BayBE learns from each shot to suggest better recipes over time.

Built with FastAPI + Jinja2/htmx + SQLite + Chart.js. Deployed as a single Docker container.

**Website:** beanbay.coffee

## Core Value

Every coffee brew teaches the system something — the app must make it effortless to capture that feedback from a phone at the espresso machine and return increasingly better recommendations.

## Current State

**Shipped:** v1 MVP (2026-02-22), v0.1.0 Release & Deploy (2026-02-22)
**Active milestone:** v0.1.1 UX Polish & Manual Brew
**Codebase:** ~7,632 LOC (Python, HTML, CSS/JS), 108 tests passing
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

### Active

See `.planning/REQUIREMENTS.md` for v0.1.1 requirements (UX polish, manual brew, responsive layout).

### Out of Scope (current milestone)

- Multi-user accounts — v3 vision
- Multi-method brewing (filter, immersion) — v2
- Grinder management with dial types — v2
- Water tracking — v2
- Beanconqueror import — v2
- Enhanced bean metadata (roast date, origin, process) — v2
- Cross-brew intelligence / recommendation from similar brews — v2
- Community/shared database — v3

## Context

- **Shipped v1:** 6 phases, 16 plans, 108 tests, ~7,632 LOC across Python/HTML/CSS/JS
- **Hardware setup:** Sage Dual Boiler (Slayer mod) + DF83v grinder. Parameters tuned to this specific machine's ranges.
- **BayBE:** Hybrid search space (5 continuous + 1 categorical), ~7.5KB campaign files. Three-phase optimization: random (0-4 shots) → Learning (5-7) → Bayesian optimization (8+).
- **Usage pattern:** Primarily phone at the espresso machine. Quick interactions most days, occasional deep tasting sessions on laptop.
- **Deployment:** Unraid server via Docker. Single container, SQLite + BayBE JSON campaign files in persistent volume. Also available to any Docker user.
- **Known tech debt:** v1 tech debt resolved in Phase 7. See milestones/v1-MILESTONE-AUDIT.md.
- **UX feedback (v0.1.1):** Navigation tabs don't scale on mobile (too many items, bean name wraps). Desktop layout is phone-sized centered — doesn't use widescreen space. Taste score defaults to 7, encouraging lazy submissions.

## Constraints

- **Backend language**: Python — BayBE is a Python library, no way around it
- **Optimization engine**: BayBE — already proven, campaign state is JSON-serializable
- **Parameters**: Fixed set of 6 parameters with current ranges (matched to Sage Dual Boiler + DF83v) — v2 will make this configurable
- **Single user**: v1/v0.1.0 is personal use only, no auth needed
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

---
*Last updated: 2026-02-22 after v0.1.1 milestone start*
