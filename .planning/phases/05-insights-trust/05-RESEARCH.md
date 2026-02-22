# Phase 5: Insights & Trust — Research

**Researched:** 2026-02-22
**Status:** Complete

## BayBE API Capabilities (v0.14.2)

### Posterior Statistics

`Campaign.posterior_stats(candidates, stats=("mean", "std"))` returns a DataFrame with predicted mean and standard deviation for given candidate points. This is the primary mechanism for understanding model confidence.

- **On measurements:** Returns fitted mean/std for existing data points. Low std = model fits well.
- **On new candidates:** Returns predicted mean/std. High std = unexplored region (high uncertainty).
- **No candidates:** If `candidates=None`, returns stats for existing measurements.

Tested output format:
```
   taste_mean  taste_std
0    6.887728   2.513343
```

### Exploration vs Exploitation Detection

`TwoPhaseMetaRecommender` uses two phases:
1. **Phase 1 (initial):** `RandomRecommender` — pure exploration, random sampling
2. **Phase 2 (after switch_after batches):** `BotorchRecommender` — Bayesian optimization with acquisition function

Detection method:
```python
from baybe.recommenders.pure.nonpredictive.sampling import RandomRecommender
selected = campaign.recommender.select_recommender(
    batch_size=1,
    searchspace=campaign.searchspace,
    objective=campaign.objective,
    measurements=campaign.measurements,
)
is_exploring = isinstance(selected, RandomRecommender)
```

With default `switch_after=1`, the first recommendation is random, then all subsequent use BO.

### Acquisition Function

After switching to BotorchRecommender, the acquisition function is `qLogExpectedImprovement`. This balances exploration and exploitation automatically — it recommends points where the expected improvement over the current best is highest, which naturally targets high-uncertainty high-mean regions.

The recommendation's posterior std relative to the average posterior std across the space indicates the explore/exploit balance:
- **std_ratio < 1:** Recommending in a relatively well-known region (exploiting)
- **std_ratio > 1:** Recommending in a relatively uncertain region (exploring)

### Convergence Signal

No built-in convergence metric in BayBE. Must be computed from available data:

1. **Mean posterior std across random grid points:** Decreases as more measurements are added (model becomes more certain everywhere). Can sample ~50 random candidates and compute mean std.
2. **Recommendation posterior std:** How uncertain the model is about its own recommendation.
3. **Recent improvement rate:** If the last N shots haven't improved the best taste, the optimizer is likely near convergence.
4. **n_batches_done / n_fits_done:** Available on Campaign object.

### Chart.js Integration

Architecture decision (from ARCHITECTURE.md Pattern 5): Charts rendered client-side with Chart.js, data passed via template-embedded JSON (`{{ chart_data | tojson }}`). No separate API endpoint needed.

Chart.js is referenced in the architecture but not yet vendored or included. It should be loaded from CDN (like htmx) for simplicity.

### Performance Considerations

- `campaign.posterior_stats()` requires a fitted surrogate model. If the campaign is in the random phase (0 measurements), there's no surrogate — will raise an error.
- Computing posterior_stats on a grid of ~50 points is fast (<1s on CPU).
- Should only compute insights when campaign has >= 2 measurements (minimum for GP fitting).
- All BayBE calls that touch the surrogate should use `asyncio.to_thread()` since they're CPU-bound.

## Key Design Decisions for Phase 5

### What to show on the recommendation page

When displaying a recommendation, add:
1. **Recommendation explanation:** "Exploring new territory" vs "Refining near your best shots" — based on whether using RandomRecommender or BotorchRecommender, and the std_ratio.
2. **Predicted taste range:** "Expected taste: 6.5-8.0" — from posterior mean ± std.
3. **Convergence indicator:** Simple text label — computed from shot count and improvement pattern.

### What to show on the insights page

A dedicated `/insights` page (or section on the brew page):
1. **Progress chart:** Line chart showing cumulative best taste over shots, with individual shot scores as scatter points (mirrors the Marimo notebook's matplotlib chart, but in Chart.js).
2. **Convergence status:** Text indicator based on heuristic rules.
3. **Optimizer phase:** "Random exploration" vs "Bayesian optimization" label.

### Convergence Heuristic

Simple rule-based convergence classification:
- **n < 3 shots:** "Getting started" — not enough data
- **n < 8 shots:** "Early exploration" — still learning the space
- **n >= 8, improvement in last 3:** "Narrowing in" — actively improving
- **n >= 8, no improvement in last 3-5:** "Likely near optimal" — convergence signal
- **n >= 8, no improvement in last 5+:** "Converged" — strong convergence signal

This avoids the computational cost of sampling the full space for posterior std and is more interpretable.

### Recommendation Explanation Logic

1. If `isinstance(selected_recommender, RandomRecommender)`: "Exploring randomly — building initial understanding of the space"
2. If BotorchRecommender and rec_posterior_std > measurements_mean_std * 1.1: "Exploring uncertain territory — the model wants to learn more about this region"
3. If BotorchRecommender and rec_posterior_std <= measurements_mean_std * 1.1: "Refining near known good recipes — the model is exploiting what it's learned"

However, computing this requires posterior_stats on the recommendation, which means we need the campaign state. The simpler and more robust approach:

**Simpler approach (recommended):** Base explanation on shot count and improvement pattern only:
1. First shot ever: "Your first experiment — exploring the space"
2. Few shots (2-4): "Building a map of the flavor space"
3. 5+ shots, best improved recently: "Zeroing in — recent shots are improving"
4. 5+ shots, best hasn't improved: "Exploring new territory — looking for something better"

This is deterministic, fast, and doesn't require BayBE computation.

**Hybrid approach (also viable):** Use the simpler approach for the text label, but add the predicted taste range from posterior_stats when available (>= 2 measurements). The posterior stats computation is fast and provides real value.

## Sources

- BayBE v0.14.2 API: Tested in local environment
- Campaign.posterior_stats: Returns mean/std DataFrame for candidates
- TwoPhaseMetaRecommender.select_recommender: Returns current active recommender
- Architecture Pattern 5 (ARCHITECTURE.md): Chart.js client-side rendering
- Existing Marimo notebook (my_espresso.py): Line 588-636 — optimization progress chart pattern

---
*Phase: 05-insights-trust*
*Research completed: 2026-02-22*
