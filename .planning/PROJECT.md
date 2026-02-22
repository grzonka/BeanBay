# BrewFlow

## What This Is

A phone-first web application for optimizing espresso recipes using Bayesian optimization (BayBE). Runs on a homeserver (Unraid/Docker), letting the user dial in any coffee bean by iterating: get a recommendation, brew, taste, rate, repeat. BayBE learns from each shot to suggest better recipes over time.

Built with FastAPI + Jinja2/htmx + SQLite + Chart.js. Deployed as a single Docker container.

## Core Value

Every espresso shot teaches the system something — the app must make it effortless to capture that feedback from a phone at the espresso machine and return increasingly better recommendations.

## Current State

**Shipped:** v1 MVP (2026-02-22)
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
- ✓ Docker deployment for Unraid homeserver — v1
- ✓ Accessible from anywhere on the local network — v1

### Active

(None yet — define with `/gsd-new-milestone`)

### Out of Scope

- Multi-user accounts — long-term vision only, not v1
- Custom parameter ranges per bean — current 6 params (grind, temp, preinfusion%, dose, yield, saturation) are fixed
- Data migration from existing Marimo app — starting fresh
- Mobile native app — webapp only
- Integration with smart scales or Bluetooth devices
- Full offline/PWA — can't run BayBE in browser, server IS the optimization engine
- SCA flavor wheel — too complex for quick phone input, 6-dimension profile sufficient

## Context

- **Shipped v1:** 6 phases, 16 plans, 108 tests, ~7,632 LOC across Python/HTML/CSS/JS
- **Hardware setup:** Sage Dual Boiler (Slayer mod) + DF83v grinder. Parameters tuned to this specific machine's ranges.
- **BayBE:** Hybrid search space (5 continuous + 1 categorical), ~7.5KB campaign files. Three-phase optimization: random (0-4 shots) → Learning (5-7) → Bayesian optimization (8+).
- **Usage pattern:** Primarily phone at the espresso machine. Quick interactions most days, occasional deep tasting sessions on laptop.
- **Deployment:** Unraid server via Docker. Single container, SQLite + BayBE JSON campaign files in persistent volume.
- **Known tech debt:** Duplicated helper, dead directory, in-memory session state, startup migration outside Alembic. See milestones/v1-MILESTONE-AUDIT.md.

## Constraints

- **Backend language**: Python — BayBE is a Python library, no way around it
- **Optimization engine**: BayBE — already proven, campaign state is JSON-serializable
- **Parameters**: Fixed set of 6 parameters with current ranges (matched to Sage Dual Boiler + DF83v)
- **Single user**: v1 is personal use only, no auth needed
- **Self-hosted**: Must run on local Unraid server via Docker

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

---
*Last updated: 2026-02-22 after v1 milestone*
