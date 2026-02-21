# BrewFlow

## What This Is

A phone-first web application for optimizing espresso recipes using Bayesian optimization. It replaces an existing Marimo notebook with a proper webapp that can run on a homeserver (Unraid/Docker), letting the user dial in any coffee bean by iterating: get a recommendation, brew, taste, rate, repeat. BayBE learns from each shot to suggest better recipes over time.

## Core Value

Every espresso shot teaches the system something — the app must make it effortless to capture that feedback from a phone at the espresso machine and return increasingly better recommendations.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Manage coffee beans (create, select, view per-bean history)
- [ ] Get BayBE-powered recipe recommendations with transparent reasoning (why this suggestion, exploration vs exploitation)
- [ ] Quick feedback flow: taste score (1-10) with optional expandable flavor profile (acidity, sweetness, body, bitterness, aroma, intensity) and notes
- [ ] Shot failure tracking (choked/gusher auto-sets taste to 1)
- [ ] Optimization progress visualization (cumulative best over time per bean)
- [ ] Parameter exploration charts (heatmaps/scatter of grind, temp, pressure vs taste)
- [ ] Cross-bean comparison (best recipes side by side)
- [ ] Brew statistics dashboard (total shots, averages, personal records)
- [ ] Mobile-first responsive UI that works well with messy hands
- [ ] Docker deployment for Unraid homeserver
- [ ] Accessible from anywhere on the local network (and potentially externally)

### Out of Scope

- Multi-user accounts — long-term vision only, not v1
- Custom parameter ranges per bean — current 6 params (grind, temp, preinfusion%, dose, yield, saturation) are fixed
- Data migration from existing Marimo app — starting fresh
- Mobile native app — webapp only
- Integration with smart scales or Bluetooth devices

## Context

- **Existing system:** Marimo notebook (`my_espresso.py`) with BayBE integration, CSV measurements, JSON campaign persistence. Works but requires laptop, no remote access, not phone-friendly.
- **Hardware setup:** Sage Dual Boiler (Slayer mod) + DF83v grinder. Parameters tuned to this specific machine's ranges.
- **BayBE:** Bayesian optimization library from EMD Group. Handles campaign state (JSON serializable), recommendation generation, and measurement ingestion. Current parameters: grind_setting (15.0-25.0), temperature (86-96C), preinfusion_pct (55-100%), dose_in (18.5-20.0g), target_yield (36-50g), saturation (yes/no). Target: taste (1-10, maximized).
- **Usage pattern:** Primarily phone at the espresso machine. Quick interactions most days, occasional deep tasting sessions on laptop. Needs to be fast and thumb-friendly.
- **Deployment:** Unraid server running Docker containers. Standard Docker Compose deployment.

## Constraints

- **Backend language**: Python — BayBE is a Python library, no way around it
- **Optimization engine**: BayBE — already proven, campaign state is JSON-serializable
- **Parameters**: Fixed set of 6 parameters with current ranges (matched to Sage Dual Boiler + DF83v)
- **Single user**: v1 is personal use only, no auth needed
- **Self-hosted**: Must run on local Unraid server via Docker

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Migrate away from Marimo | Marimo requires laptop, no phone support, no remote access | — Pending |
| Start fresh (no data migration) | Existing data is limited, clean start preferred | — Pending |
| Phone-first UI design | Primary usage is at the espresso machine with phone | — Pending |
| Quick + expandable feedback | Fast taste score by default, optional flavor breakdown for deep sessions | — Pending |
| Docker deployment on Unraid | Matches existing homeserver infrastructure | — Pending |
| Transparent recommendations | Show why BayBE suggests a recipe (exploration vs exploitation, uncertainty) | — Pending |

---
*Last updated: 2026-02-21 after initialization*
