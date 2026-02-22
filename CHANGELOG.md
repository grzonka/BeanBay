# Changelog

## v0.1.0 — Initial Release (2026-02-22)

First public release of BeanBay — a self-hosted espresso optimization app powered by Bayesian learning.

### Features
- Phone-first web UI for espresso recipe optimization
- BayBE-powered recommendations (hybrid search space, 3-phase learning)
- Bean management with per-bean optimization campaigns
- Shot history with filtering, detail modals, and retroactive editing
- 6-dimension flavor profiles (acidity, sweetness, body, bitterness, aroma, intensity)
- Insights dashboard with Chart.js progress charts and convergence badges
- Parameter exploration heatmaps
- Analytics with aggregate brew statistics and cross-bean comparison
- Dark espresso theme with 48px+ touch targets
- Docker deployment (single container, SQLite + BayBE)

### Infrastructure
- GitHub Actions CI (test on PR/push, Docker publish on tags)
- Docker image published to ghcr.io/grzonka/beanbay
- Apache 2.0 license
