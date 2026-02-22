# Phase 5: Insights & Trust — Context

**Gathered:** 2026-02-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can see that the optimizer is learning and understand why it suggests what it suggests — building confidence to keep experimenting. This covers:

- Progress visualization (cumulative best taste chart)
- Recommendation explanation (exploring vs exploiting)
- Convergence indicator (how far along the optimization is)

Data collection, shot recording, and the core optimize loop are Phases 3-4 (complete). Parameter heatmaps, cross-bean comparison, and aggregate statistics are Phase 6.

</domain>

<decisions>
## Implementation Decisions

### Progress Chart

- Chart.js line chart showing cumulative best taste score over shot number for the active bean
- Individual shot scores shown as scatter points beneath the cumulative best line
- Chart appears on a dedicated insights page (`/insights`) and is also available from the brew page as a link
- Data passed via template-embedded JSON (`{{ chart_data | tojson }}`) — no separate API endpoint
- Chart.js loaded from CDN (consistent with htmx CDN pattern)
- Chart only renders when bean has >= 2 non-failed measurements
- Dark theme styling to match app theme (dark backgrounds, accent color for the cumulative best line)

### Recommendation Explanation

- Shown on the recommendation display page (`/brew/recommend/{id}`) alongside the recipe card
- Two-part display:
  1. **Phase label:** "Random exploration" or "Bayesian optimization" — based on which recommender is active (RandomRecommender vs BotorchRecommender)
  2. **Contextual explanation:** Plain language text based on shot count and recent improvement pattern
- Predicted taste range shown when available (posterior_stats mean ± std), formatted as "Expected taste: ~6.5 (range 4.5-8.5)"
- The recommendation already stores parameters in `pending_recommendations` dict — extend to include insight metadata computed at recommendation time

### Convergence Indicator

- Heuristic-based text label displayed on insights page and optionally on brew page
- Rules (applied in order):
  - n < 3 shots: "Getting started"
  - n < 8 shots: "Early exploration"
  - n >= 8, best improved in last 3 shots: "Narrowing in"
  - n >= 8, no improvement in last 5+ shots: "Likely near optimal"
  - n >= 8, no improvement in last 3-5 shots: "Refining"
- Color-coded badge: exploration=blue-ish, narrowing=amber, converged=green
- No BayBE posterior computation needed — purely measurement-history based

### Insights Page

- New route: `GET /insights`
- Shows insights for the active bean (requires active bean, redirect to /beans if none)
- Content:
  1. Bean name + total shot count header
  2. Convergence status badge + explanation text
  3. Optimizer phase (random vs BO)
  4. Progress chart (Chart.js)
  5. Best recipe quick-view (link to /brew/best)
- Add "Insights" link to main navigation

### BayBE Integration Points

- `OptimizerService.get_recommendation_insights(bean_id, rec_dict)` — new method returning insight metadata:
  - `is_exploring`: bool (RandomRecommender vs BotorchRecommender)
  - `predicted_mean`: float | None (from posterior_stats)
  - `predicted_std`: float | None (from posterior_stats)
  - Only computed when campaign has >= 2 measurements (GP needs data)
- Insight computation happens at recommend time (not at display time) — stored in pending_recommendations alongside recipe params
- Thread-safe: all BayBE calls within existing lock

### OpenCode's Discretion

- Exact Chart.js configuration options (animation, gridlines, point styles)
- Chart responsive behavior details
- Convergence badge visual styling
- Whether to show the convergence indicator on the brew index page (in addition to insights page)
- Exact wording of recommendation explanations
- Whether predicted taste range uses ± or shows as a range

</decisions>

<specifics>
## Specific Ideas

- Progress chart pattern from Marimo notebook (my_espresso.py lines 588-636): cumulative best line + individual shot scatter + "excellent" threshold line at 8.5
- "Early recommendations are random (exploration); as you add measurements the model switches to Bayesian optimization (exploitation)" — from Marimo UI text
- Mobile-first as established: 48px+ touch targets, 375px primary width, dark espresso theme
- Chart.js responsive mode with maintainAspectRatio: false for mobile

</specifics>

<deferred>
## Deferred Ideas

- **Posterior uncertainty sampling across parameter space** — Computing posterior_stats on a grid of ~50 random candidates to get a more accurate explore/exploit signal. The simpler heuristic approach is sufficient for v1; this can be added later if users want more granular insight.
- **Interactive chart with tap-to-view-shot** — Tapping a data point on the progress chart opens the shot detail modal. Requires Chart.js click event handling + htmx integration. Nice-to-have but not required for Phase 5.
- **Parameter sensitivity display** — Showing which parameters the model thinks matter most (from GP lengthscales). Requires deeper BayBE surrogate introspection. Phase 6 territory.

</deferred>

---

*Phase: 05-insights-trust*
*Context gathered: 2026-02-22*
