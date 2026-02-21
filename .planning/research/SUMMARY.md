# Research Summary: BrewFlow

**Domain:** Phone-first espresso optimization webapp with Bayesian optimization (BayBE)
**Researched:** 2026-02-21
**Overall confidence:** HIGH

## Executive Summary

BrewFlow transforms an existing Marimo notebook into a phone-first web application for espresso recipe optimization. The research surveyed the competitive landscape (Beanconqueror, Decent DE1 App), the BayBE optimization engine's constraints and capabilities, technology options for a self-hosted Python webapp, and the domain-specific pitfalls of building an optimization tool for messy-handed, pre-coffee users at an espresso machine.

**The single most important finding:** No existing coffee app does AI-powered recipe optimization. Every competitor (Beanconqueror, Decent, Gaggiuino) is a tracking tool — they record what you did but never suggest what to try next. This means BrewFlow has a clear differentiator but no UX precedent to copy. The closest UX analogues come from optimization dashboards (Optuna, W&B) rather than coffee apps, and those are all desktop-first.

**The critical architectural challenge** is BayBE's campaign serialization: each bean's campaign JSON is ~20MB (147,840-row discrete search space serialized as pickled binary blobs). This dominates every backend design decision — in-memory caching, async I/O, measurements-as-source-of-truth, and the discrete-vs-continuous parameter choice. Getting this wrong means 3-5 second I/O per request, fragile version coupling, and a 200MB data directory for just 10 beans.

**The recommended stack** is deliberately simple: FastAPI + Jinja2 + htmx + SQLite + Chart.js, deployed as a single Docker container. No JavaScript framework, no separate frontend repo, no build toolchain. This stack respects the constraint that this is a single-user personal tool with ~5 screens, while providing the async capabilities needed for BayBE's 3-10 second `recommend()` calls.

## Key Findings

**Stack:** FastAPI + Jinja2/htmx + SQLite + Chart.js in a single Docker container. No JS framework needed. CPU-only PyTorch saves ~1GB in the Docker image.

**Architecture:** Monolithic server-rendered app with dual storage (SQLite for queryable data, JSON files for BayBE campaign state). Measurements in SQLite are the source of truth; campaigns are a rebuildable cache.

**Critical pitfall:** BayBE campaign files are 20MB of pickled binary, fragile across version upgrades. Must architect around this from day one — in-memory cache, measurements-as-source-of-truth, campaign rebuild mechanism.

**Competitive gap:** Zero existing coffee apps do AI-powered optimization. BrewFlow's value proposition is unique and defensible.

**UX constraint:** Users have wet/messy hands, are standing with phone in one hand, are pre-coffee, and have 60-90 second interaction windows. This eliminates sliders, small touch targets, multi-step wizards, and anything requiring precise gestures.

## Implications for Roadmap

Based on research, the project naturally decomposes into 4-5 phases aligned with the dependency graph in FEATURES.md and the pitfall-to-phase mapping in PITFALLS.md:

### Suggested Phase Structure

1. **Phase 1: Foundation (Data Layer + Project Skeleton)** — Set up the project structure, database schema, BayBE integration layer, and campaign management.
   - Addresses: Project structure, SQLAlchemy models (beans, measurements), campaign store with in-memory cache, BayBE service wrapper, Alembic migrations, basic configuration.
   - Avoids: Pitfall #1 (campaign size via caching), #2 (version fragility via measurements-as-source-of-truth), #5 (search space explosion — decide discrete vs continuous now), #9 (CSV corruption — use SQLite), #12 (bean name collisions — use UUIDs).
   - Rationale: Architecture decisions made here are the most expensive to change later. The data model, parameter type (discrete vs continuous), and storage pattern affect every subsequent phase.

2. **Phase 2: Core Loop (Recommend → Brew → Rate)** — The minimum usable product. Phone-first UI for the complete optimization cycle.
   - Addresses: Features T1 (bean management), T2 (recommendation display), T3 (taste score input), T4 (shot history), T5 (shot failure), T7 (brew ratio), T8 (mobile-first layout), D8 (notes), D9 (shot time).
   - Avoids: Pitfall #3 (async recommend with loading indicator), #4 (double-submission via idempotency tokens), #7 (phone UX via large touch targets), #8 (cold start via exploration explanation).
   - Rationale: This is the MVP. After this phase, the app is usable at the espresso machine. Everything else is enhancement.

3. **Phase 3: Insights & Trust** — Visualization and transparency features that help users understand and trust the optimization.
   - Addresses: Features T6 (optimization progress chart), D1 (transparent reasoning), D2 (expandable flavor profile), D6 (exploration/exploitation indicator), D7 (repeat best action).
   - Avoids: Pitfall #6 (taste subjectivity via calibration aids), #11 (mobile charts via Chart.js responsive design).
   - Rationale: These features make the difference between "I used it once" and "I use it every morning." Trust in the optimizer drives retention.

4. **Phase 4: Analytics & Polish** — Cross-bean insights, statistics, and UX refinements.
   - Addresses: Features D3 (parameter heatmaps), D4 (cross-bean comparison), D5 (brew statistics dashboard).
   - Rationale: These features need accumulated data across multiple beans to be valuable. By this phase, the user has enough history for meaningful analytics.

5. **Phase 5: Deployment Hardening** — Docker optimization, backup/restore, production readiness.
   - Addresses: Docker image optimization (CPU-only PyTorch, multi-stage build), volume mount configuration, backup/export endpoint, health checks.
   - Avoids: Pitfall #10 (Docker image bloat — target <1.5GB), #13 (backup strategy).
   - Rationale: Can be done in parallel with Phase 2-3 development, but deployment hardening is its own concern.

### Phase Ordering Rationale

- **Phase 1 before everything:** Architecture decisions (discrete vs continuous params, SQLite schema, campaign caching strategy) are expensive to change. Get them right first.
- **Phase 2 is the MVP:** The recommend→brew→rate loop is the entire value proposition. No point building analytics before the core loop works.
- **Phase 3 before Phase 4:** Trust features (transparent reasoning, progress visualization) drive daily usage. Analytics (heatmaps, cross-bean) require accumulated data that only exists if Phase 3 keeps users engaged.
- **Phase 5 can overlap:** Docker and deployment can be developed alongside Phase 2-3, but final hardening (image size optimization, backup strategy) comes last.

### Research Flags for Phases

- **Phase 1:** Likely needs deeper research on **discrete vs continuous BayBE parameters**. Switching from `NumericalDiscreteParameter` to `NumericalContinuousParameter` would eliminate the 147,840-row search space explosion and 20MB campaign files, but may change recommendation behavior. Need to test with BayBE to verify continuous parameter support with the existing parameter definitions.
- **Phase 2:** Standard patterns — htmx form handling, FastAPI routing, Jinja2 templates. Unlikely to need additional research.
- **Phase 3:** May need research on **extracting uncertainty/confidence data from BayBE's surrogate model** for the transparent reasoning feature (D1). BayBE's API for accessing posterior mean/variance is not well-documented.
- **Phase 5:** Standard Docker patterns. May need testing for CPU-only PyTorch installation specifics.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technologies verified via official docs. FastAPI + htmx + SQLite is a proven pattern. BayBE version confirmed in existing codebase. |
| Features | HIGH | Feature landscape derived from direct competitor analysis (Beanconqueror, Decent) + existing Marimo prototype code review. UX patterns from established mobile guidelines (Apple HIG, Material Design). |
| Architecture | HIGH | Architecture patterns grounded in verified BayBE behavior (20MB campaign files, 3-10s recommend times) and standard FastAPI patterns. Dual storage pattern is a direct response to verified pitfalls. |
| Pitfalls | HIGH | 10 of 13 pitfalls verified against actual codebase artifacts (campaign file size, parameter counts, BayBE serialization format). Remaining 3 based on standard web development knowledge. |

## Gaps to Address

- **Discrete vs continuous parameters:** The most impactful unresolved question. Continuous parameters would simplify campaign size dramatically but need BayBE compatibility testing with the existing parameter definitions (especially `saturation` which is categorical, and `preinfusion_pct` which has only 4 values). This should be investigated early in Phase 1.
- **BayBE surrogate model access:** For the transparent reasoning feature (D1), we need to determine what information can be extracted from BayBE's internal GP model (uncertainty, acquisition function values, feature importance). The BayBE docs are sparse on this. Phase 3 research.
- **BayBE `allow_recommending_already_recommended` bug (#733):** Confirmed bug in BayBE 0.14.2's recommendation cache check. Need to verify if a workaround exists or if this is fixed in a newer version. Could affect recommendation behavior when the search space is well-explored.
- **htmx + FastAPI integration patterns:** While both are well-documented individually, specific patterns for htmx partial rendering with FastAPI/Jinja2 (detecting `HX-Request` header, returning fragments vs full pages) should be validated with a quick prototype at the start of Phase 2.
- **Chart.js responsive behavior on very small screens (375px):** Chart.js is responsive by default, but espresso parameter heatmaps on a 375px screen may need custom configuration for readability. Test in Phase 3.

## Cross-Reference Summary

| Research File | Key Takeaway | Phase Impact |
|---------------|--------------|--------------|
| FEATURES.md | 9 MVP features, 9 differentiators, 11 anti-features. Critical path: T1→T2→T3→T4→T6. No competitor does AI optimization. | Defines what to build in each phase. MVP is the recommend-rate loop. |
| PITFALLS.md | 13 pitfalls mapped to phases. Top 5 are all architectural (campaign size, version fragility, async recommend, double-submit, search space explosion). | Defines what to avoid. Phase 1 must address 5 critical pitfalls. |
| STACK.md | FastAPI + htmx + SQLite + Chart.js. No JS framework. CPU-only PyTorch. uv for package management. | Technology decisions are settled. No open questions. |
| ARCHITECTURE.md | Monolith, dual storage, 5 key patterns (measurements-as-truth, campaign cache, htmx partials, idempotent submissions, progressive chart enhancement). | System structure is defined. Project directory layout is specified. |

---
*Research summary for: BrewFlow — Phone-first espresso optimization webapp with BayBE*
*Researched: 2026-02-21*
