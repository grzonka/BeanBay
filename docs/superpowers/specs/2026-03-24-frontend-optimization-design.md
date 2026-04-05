# Frontend Optimization UX — Design Spec

## Overview

Frontend integration for BayBE optimization in the BeanBay React SPA. Adds a "Suggest" button to the BrewWizard, a campaign list/detail dashboard with 8 chart visualizations powered by Plotly, and a per-person preferences page. Requires two new backend endpoints (posterior predictions + feature importance) and a fix to populate predicted score/std on recommendations.

## Key Design Decisions

| # | Topic | Decision |
|---|---|---|
| 1 | Page structure | Campaign list (`/optimize`) + detail (`/optimize/:campaignId`) pages |
| 2 | BrewWizard integration | "Suggest" button on Step 2 (Parameters), campaigns auto-created transparently |
| 3 | Visualizations | All 8: score progress, parameter heatmap, 1D sweeps, 2D prediction surface, SHAP importance, uncertainty surface, recommendation history, convergence stats |
| 4 | Parameter selectors | Per-chart dropdowns with sensible defaults (SHAP-driven or method-based fallback) |
| 5 | Person preferences | Dedicated `/people/:personId/preferences` page, accessed from People list row click |
| 6 | Chart library | Replace Recharts with Plotly (`react-plotly.js` + `plotly.js-dist-min`), single library |
| 7 | New backend endpoints | One flexible `/posterior` endpoint + `/feature-importance` endpoint |

## New Backend Endpoints

### Posterior Predictions

Flexible endpoint powering 1D sweeps, 2D surfaces, and uncertainty visualizations.

```
GET /api/v1/optimize/campaigns/{campaign_id}/posterior
    Query params:
      params: str          — comma-separated parameter names (1 or 2)
      points: int = 30     — grid resolution per dimension

    Response: {
      params: ["temperature"],                    // or ["grind_setting", "temperature"]
      grid: [[85.0, 86.0, 87.0, ...]],           // 1 array per param (axis values)
      mean: [7.2, 7.4, 7.1, ...],                // 1D array or 2D nested array
      std: [0.3, 0.2, 0.4, ...],                 // same shape as mean
      measurements: [                             // actual data points for overlay
        {values: {temperature: 93.0, ...}, score: 8.1},
        ...
      ]
    }
```

**Implementation:** Load the campaign's BayBE state from `campaign_json`. Build a grid of points across the requested parameter(s), holding all other parameters at their best-known values (from the highest-scoring measurement). Call `campaign.posterior_stats(grid_df)` to get mean and std at each point. Return alongside actual measurements for overlay.

**1D usage:** `?params=temperature&points=50` — returns 1D arrays for mean/std. Frontend renders as area chart with uncertainty band.

**2D usage:** `?params=grind_setting,temperature&points=20` — returns 2D arrays (20x20). Frontend renders as contour heatmap.

**Minimum data:** Requires at least 2 valid measurements. Returns 422 if insufficient data.

### Feature Importance (SHAP)

```
GET /api/v1/optimize/campaigns/{campaign_id}/feature-importance
    Response: {
      parameters: ["temperature", "grind_setting", "dose", ...],
      importance: [0.42, 0.31, 0.15, ...],
      measurement_count: 14
    }
```

**Implementation:** Load BayBE campaign from `campaign_json`. Call `SHAPInsight.from_campaign(campaign)`. Extract SHAP values per parameter. Sort by importance descending.

**Minimum data:** Requires at least 3 valid measurements (enough to fit a basic GP). Returns 422 if insufficient data. Results improve with more data.

### Backend Fix: Populate Predicted Score/Std

The `Recommendation` model has `predicted_score` and `predicted_std` columns that are never populated. Fix the taskiq worker (`src/beanbay/services/taskiq_broker.py`) to call `campaign.posterior_stats(rec_df)` after generating a recommendation and store the results:

```python
# After campaign.recommend(batch_size=1)
stats = baybe_campaign.posterior_stats(rec_df)
predicted_score = float(stats["score_Mean"].iloc[0])
predicted_std = float(stats["score_Std"].iloc[0])

# Set on Recommendation row
rec.predicted_score = predicted_score
rec.predicted_std = predicted_std
```

Only populate when the campaign has 2+ measurements (posterior stats not meaningful before that).

## Frontend Pages & Routes

### New Routes

| Route | Component | Purpose |
|---|---|---|
| `/optimize` | `CampaignListPage` | Overview of all optimization campaigns |
| `/optimize/:campaignId` | `CampaignDetailPage` | Full analytics dashboard with 8 charts |
| `/people/:personId/preferences` | `PersonPreferencesPage` | Per-person bean preference analytics |

### Modified Components

| Component | Change |
|---|---|
| `BrewWizard.tsx` | Add "Suggest" button on Step 2, auto-create campaign + poll recommendation |
| `PeoplePage.tsx` | Row click navigates to `/people/:id/preferences` (was: open edit dialog) |
| `TasteRadar.tsx` | Migrate from Recharts to Plotly |
| `DashboardPage.tsx` | Add "Active Campaigns" summary card linking to `/optimize` |
| `App.tsx` | Add new routes |

### Package Changes

| Action | Package |
|---|---|
| Remove | `recharts` |
| Add | `react-plotly.js`, `plotly.js-dist-min` |

## BrewWizard "Suggest" Integration

### UX Flow

On Step 2 (Parameters), a "Get Suggestion" button (outlined/secondary style) appears alongside the parameter input fields.

**When clicked:**

1. Resolve `bag_id → bean_id` from the bag data already loaded in Step 1
2. `POST /api/v1/optimize/campaigns` with `{bean_id, brew_setup_id}` — creates or returns existing campaign (idempotent)
3. `POST /api/v1/optimize/campaigns/{id}/recommend` — starts async job, returns `{job_id}`
4. Poll `GET /api/v1/optimize/jobs/{job_id}` until status is `completed` or `failed`
5. On completion: `GET /api/v1/optimize/recommendations/{recommendation_id}` — get parameter values
6. Auto-fill parameter fields with recommended values
7. Show info banner: "Suggested by optimizer (shot #15, learning phase)" with predicted score if available: "Predicted: ~7.8 (7.1 - 8.5)"

**On brew save:**

8. `POST /api/v1/brews` as normal (existing flow)
9. `POST /api/v1/optimize/recommendations/{id}/link` with `{brew_id}` — links the brew to the recommendation

### Button States

- **Idle**: "Get Suggestion" (outlined button)
- **Loading**: spinner + "Computing..." (disabled)
- **Filled**: fields highlighted with light blue border, banner shown
- **Error**: toast notification, fields remain empty for manual entry

### Edge Cases

- **No grinder on setup**: `grind_setting` not in suggestion, field stays empty
- **Preground bag**: same as above
- **First suggestion (0 measurements)**: random exploration, no predicted score shown
- **Job fails**: error toast, user enters params manually
- **Outcome fields** (e.g. `total_time` for espresso is measured after brewing): left empty

### Campaign Auto-Creation

Campaigns are always created automatically — the user never explicitly "creates a campaign." They just click "Suggest" and it works. The campaign is an implementation detail scoped to (bean, brew_setup).

## Campaign List Page

`/optimize` — shows all campaigns that exist, created automatically via BrewWizard suggestions.

### Layout

Each campaign row shows:
- Bean name + brew method/setup name
- Best score badge (color-coded: green 8+, amber 6-8, red <6)
- Shot count
- Phase indicator (random / learning / optimizing)
- Convergence progress bar

Row click navigates to `/optimize/:campaignId`.

No "Create Campaign" button — campaigns are created automatically from the BrewWizard.

### Data Source

`GET /api/v1/optimize/campaigns` — already exists.

## Campaign Detail Page

`/optimize/:campaignId` — scrollable page with stats header + 8 chart sections.

### Stats Header

Three stat cards at the top:
- **Phase**: current optimization phase with badge (random=blue, learning=amber, optimizing=green)
- **Shots / Best**: measurement count and best score
- **Convergence**: status text + improvement rate

Data source: `GET /api/v1/optimize/campaigns/{id}/progress`

### Chart 1: Score Progress

**Type:** Plotly Scatter (individual scores) + Line (cumulative best)

**Data:** `GET /api/v1/optimize/campaigns/{id}/progress` → `score_history[]`

- X axis: shot number
- Y axis: taste score (1-10)
- Green line: cumulative best score over time
- Amber dots: individual shot scores
- Red X markers: failed shots
- Hover: shot number, score, failed status

### Chart 2: Parameter Exploration Heatmap

**Type:** Plotly Scatter with `marker.color` mapped to score, `colorscale: 'RdYlGn'`

**Data:** `GET /api/v1/brews` filtered by bean + brew_setup (existing endpoint)

- X/Y axes: user-selectable parameters via dropdowns
- Dot color: taste score (red→amber→green)
- Gray X markers: failed shots
- Color bar: score scale 1-10

**Default axes:** Two most important parameters (from SHAP), or `grind_setting` + `temperature` as fallback.

### Charts 3-4: 1D Parameter Sweeps

**Type:** Plotly Line (mean) + filled area (mean ± std band)

**Data:** `GET /api/v1/optimize/campaigns/{id}/posterior?params={param}&points=50`

- X axis: parameter value range
- Y axis: predicted score
- Blue line: posterior mean
- Light blue band: ±1 std uncertainty
- Amber dots: actual measurements overlaid

**Auto-generated** for the top 4 parameters by SHAP importance. If SHAP unavailable (<3 measurements), show sweeps for all active non-categorical parameters. Each sweep holds other parameters at their best-known values.

### Chart 5: 2D Prediction Surface

**Type:** Plotly `Contour` or `Heatmap` with `colorscale: 'RdYlGn'`

**Data:** `GET /api/v1/optimize/campaigns/{id}/posterior?params={x},{y}&points=20`

- X/Y axes: user-selectable parameters via dropdowns
- Color: predicted score (mean)
- White dots overlaid: actual measurements
- Color bar: predicted score scale

**Default axes:** same as parameter heatmap defaults.

### Chart 6: Feature Importance (SHAP)

**Type:** Plotly horizontal `Bar`

**Data:** `GET /api/v1/optimize/campaigns/{id}/feature-importance`

- Y axis: parameter names (sorted by importance)
- X axis: SHAP importance value
- Single color (blue)

**Minimum data:** Only shown when ≥3 measurements. Shows "Need more data" placeholder otherwise.

### Chart 7: Uncertainty Surface

**Type:** Plotly `Contour` or `Heatmap` with sequential colorscale (dark blue → yellow)

**Data:** Same `GET /posterior` endpoint — frontend maps `std` array instead of `mean`

- X/Y axes: user-selectable parameters via dropdowns (independent from prediction surface)
- Color: prediction uncertainty (std) — dark = confident, bright = uncertain
- Shows where the model needs more data

**Default axes:** same as prediction surface defaults.

### Chart 8: Recommendation History

**Type:** MUI DataGrid (existing DataTable component)

**Data:** `GET /api/v1/optimize/campaigns/{id}/recommendations`

Columns:
- `#` (sequential)
- Phase badge
- Key parameter values (top 3-4)
- Predicted score ± std
- Status (pending / brewed / skipped)
- Linked brew score (if brewed)
- Created timestamp

### Parameter Selector Pattern

Charts that need parameter selection (heatmap, 2D surface, uncertainty surface) each have their own X/Y axis dropdown selectors above the chart. Selectors are independent — changing one chart's axes doesn't affect others.

**Sensible defaults:**
- If SHAP data is available (≥3 measurements): pre-select the two most important parameters
- If not enough data for SHAP: default to `grind_setting` + `temperature` for espresso-type methods, `grind_setting` + `dose` for filter methods
- Available parameters populated from the campaign's `effective_ranges` (from campaign detail endpoint)

**1D sweeps** are auto-selected — no user dropdowns. Show top 4 params by SHAP importance, or all active non-categorical params if SHAP unavailable.

## Person Preferences Page

`/people/:personId/preferences` — accessed by clicking a person row in the People list.

### Layout

**Stats header** (3 cards):
- Total brews
- Average score
- Favorite method (by brew count)

**Charts** (all Plotly):

1. **Top Beans** — horizontal bar chart, sorted by avg score, brew count as annotation. Data: `top_beans[]`
2. **Flavor Profile** — radar chart (`Scatterpolar`), tag frequencies as dimensions. Data: `flavor_profile[]`
3. **Roast Preference** — donut chart (`Pie` with hole), light/medium/dark distribution. Data: `roast_preference{}`
4. **Origin Preferences** — horizontal bar chart, sorted by avg score. Data: `origin_preferences[]`
5. **Method Breakdown** — grouped bar chart (brew count + avg score per method). Data: `method_breakdown[]`

### Data Source

Single endpoint: `GET /api/v1/optimize/people/{id}/preferences` — already exists and returns all needed data.

### People Page Change

Currently, clicking a person row opens an edit dialog. Change: row click navigates to `/people/:id/preferences`. The preferences page includes an "Edit" button in the header that opens the same edit dialog.

## Modified Existing Components

### TasteRadar.tsx Migration

Replace Recharts `RadarChart` with Plotly `Scatterpolar`. Same visual result (radar chart of sensory scores), different library. Used on brew detail and cupping detail pages.

### DashboardPage.tsx

Add an "Optimization" section with a summary card showing:
- Number of active campaigns
- Best overall score across campaigns
- Link to `/optimize`

Data: `GET /api/v1/optimize/campaigns` (count + max best_score from results).

## File Structure

### New Frontend Files

| File | Responsibility |
|------|---------------|
| `features/optimize/pages/CampaignListPage.tsx` | Campaign list with status cards |
| `features/optimize/pages/CampaignDetailPage.tsx` | Stats header + 8 chart sections |
| `features/optimize/hooks.ts` | React Query hooks for all optimization endpoints |
| `features/optimize/components/ScoreProgressChart.tsx` | Chart 1: line + scatter |
| `features/optimize/components/ParameterHeatmap.tsx` | Chart 2: colored scatter |
| `features/optimize/components/ParameterSweepChart.tsx` | Charts 3-4: area with band |
| `features/optimize/components/PredictionSurface.tsx` | Chart 5: contour heatmap |
| `features/optimize/components/FeatureImportance.tsx` | Chart 6: horizontal bar |
| `features/optimize/components/UncertaintySurface.tsx` | Chart 7: contour heatmap |
| `features/optimize/components/RecommendationHistory.tsx` | Chart 8: DataTable |
| `features/optimize/components/ParamSelector.tsx` | Reusable X/Y axis dropdown pair |
| `features/optimize/components/SuggestButton.tsx` | BrewWizard suggest integration |
| `features/people/pages/PersonPreferencesPage.tsx` | Preference analytics page |
| `features/people/components/TopBeansChart.tsx` | Horizontal bar chart |
| `features/people/components/FlavorRadar.tsx` | Radar chart |
| `features/people/components/RoastDonut.tsx` | Donut chart |
| `features/people/components/OriginPreferences.tsx` | Horizontal bar chart |
| `features/people/components/MethodBreakdown.tsx` | Grouped bar chart |
| `components/PlotlyChart.tsx` | Thin wrapper around react-plotly.js with theme defaults |

### Modified Frontend Files

| File | Change |
|------|--------|
| `App.tsx` | Add routes for `/optimize`, `/optimize/:campaignId`, `/people/:personId/preferences` |
| `features/brews/components/BrewWizard.tsx` | Add SuggestButton integration on Step 2 |
| `features/brews/components/BrewStepParams.tsx` | Accept and display suggestion state (highlighted fields, info banner) |
| `features/people/pages/PeoplePage.tsx` | Row click → navigate to preferences |
| `features/dashboard/DashboardPage.tsx` | Add optimization summary card |
| `components/TasteRadar.tsx` | Migrate from Recharts to Plotly |

### New Backend Files

| File | Change |
|------|--------|
| `src/beanbay/routers/optimize.py` | Add `get_posterior()` and `get_feature_importance()` endpoints |
| `src/beanbay/schemas/optimization.py` | Add `PosteriorResponse` and `FeatureImportanceResponse` schemas |
| `src/beanbay/services/taskiq_broker.py` | Fix: populate `predicted_score`/`predicted_std` on Recommendation |
