# Project Milestones: BeanBay

## v1 MVP (Shipped: 2026-02-22)

**Delivered:** Phone-first espresso optimization app powered by Bayesian optimization — manage beans, get BayBE-powered recipe recommendations, rate shots, track history, and visualize optimization progress, all from a phone at the espresso machine.

**Phases completed:** 1-6 (16 plans total)

**Key accomplishments:**
- Full BayBE-powered espresso optimization loop — recommend, brew, rate, repeat — with hybrid search space (7.5KB campaigns vs 20MB discrete)
- Mobile-first dark espresso theme with 48px+ touch targets, usable with wet hands at the machine
- Shot history with filtering, detail modals, retroactive editing, and expandable 6-dimension flavor profiles
- Insights dashboard with Chart.js progress charts, 3-phase convergence badges, and parameter exploration heatmaps
- Analytics page with aggregate brew statistics and cross-bean best recipe comparison
- Docker deployment ready for Unraid homeserver (FastAPI + SQLite + BayBE in single container)

**Stats:**
- 108 files created/modified
- ~7,632 lines of code (Python, HTML, CSS/JS)
- 6 phases, 16 plans, 108 tests
- 1 day from start to ship (Feb 21-22, 2026)

**Git range:** `docs: initialize project` → `docs(v1): create milestone audit report`

---

## v1.1 Release & Deploy (In Progress)

**Goal:** Rebrand from BrewFlow to BeanBay, clean up tech debt, create documentation, and ship as a publicly deployable product with Docker images and Unraid support.

**Phases:** 7-9 (5 plans total)

**Key deliverables:**
- Rebrand: BrewFlow → BeanBay (beanbay.coffee)
- Tech debt cleanup (5 items from v1 audit)
- README, LICENSE, GitHub Actions CI/CD
- Docker image on ghcr.io/grzonka/beanbay
- Unraid Community Apps XML template

**Status:** Planning complete, ready for execution.

---
