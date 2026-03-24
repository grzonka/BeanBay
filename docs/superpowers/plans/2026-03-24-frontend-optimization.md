# Frontend Optimization UX — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add BayBE optimization UI to BeanBay — BrewWizard "Suggest" button, campaign analytics dashboard with 8 chart types, and person preference analytics. Requires two new backend endpoints, a taskiq worker fix, and a full React frontend with Plotly charts.

**Architecture:** Backend-first — add `/posterior` and `/feature-importance` endpoints to the existing optimize router, fix the taskiq worker to populate predicted scores, then build the React frontend. Frontend replaces Recharts with Plotly via a thin wrapper, organized as a new `features/optimize` module following existing patterns (React Query hooks, MUI components, `sx` styling).

**Tech Stack:** Python 3.12 / FastAPI / SQLModel (backend), BayBE `posterior_stats` + `SHAPInsight` (ML), React 19 / TypeScript / MUI v7 / `react-plotly.js` + `plotly.js-dist-min` (frontend), React Query v5 (data fetching), bun (package manager)

---

## Scope Note

This spec covers two independent subsystems:

- **Backend** (Tasks 1–4): New schemas, two analytical endpoints, taskiq fix — fully testable via `pytest` integration tests
- **Frontend** (Tasks 5–19): Plotly infrastructure, campaign pages, suggest button, person preferences, existing component mods — testable via dev server + `bun run build`

Each subsystem produces working, testable software independently. Backend can ship first; frontend builds on its APIs.

---

## File Structure

### Modified Backend Files

| File | Change |
|------|--------|
| `src/beanbay/schemas/optimization.py` | Add `MeasurementPoint`, `PosteriorResponse`, `FeatureImportanceResponse` schemas |
| `src/beanbay/routers/optimize.py` | Add `get_posterior()` and `get_feature_importance()` endpoints |
| `src/beanbay/services/taskiq_broker.py` | Populate `predicted_score` / `predicted_std` on Recommendation |
| `tests/integration/test_optimize_api.py` | Add tests for new endpoints and taskiq fix |

### New Frontend Files

| File | Responsibility |
|------|---------------|
| `frontend/src/components/PlotlyChart.tsx` | Thin wrapper around `react-plotly.js` with MUI theme defaults |
| `frontend/src/features/optimize/hooks.ts` | React Query hooks for all optimization endpoints |
| `frontend/src/features/optimize/pages/CampaignListPage.tsx` | Campaign list with status cards |
| `frontend/src/features/optimize/pages/CampaignDetailPage.tsx` | Stats header + 8 chart sections |
| `frontend/src/features/optimize/components/ScoreProgressChart.tsx` | Chart 1: scatter + cumulative best line |
| `frontend/src/features/optimize/components/ParamSelector.tsx` | Reusable X/Y axis dropdown pair |
| `frontend/src/features/optimize/components/ParameterHeatmap.tsx` | Chart 2: colored scatter plot |
| `frontend/src/features/optimize/components/ParameterSweepChart.tsx` | Charts 3–4: line + uncertainty band |
| `frontend/src/features/optimize/components/PredictionSurface.tsx` | Chart 5: contour heatmap (mean) |
| `frontend/src/features/optimize/components/FeatureImportance.tsx` | Chart 6: horizontal bar |
| `frontend/src/features/optimize/components/UncertaintySurface.tsx` | Chart 7: contour heatmap (std) |
| `frontend/src/features/optimize/components/RecommendationHistory.tsx` | Chart 8: DataTable |
| `frontend/src/features/optimize/components/SuggestButton.tsx` | BrewWizard suggest integration |
| `frontend/src/features/people/pages/PersonPreferencesPage.tsx` | Preference analytics page |
| `frontend/src/features/people/components/TopBeansChart.tsx` | Horizontal bar chart |
| `frontend/src/features/people/components/FlavorRadar.tsx` | Plotly radar chart |
| `frontend/src/features/people/components/RoastDonut.tsx` | Donut chart |
| `frontend/src/features/people/components/OriginPreferences.tsx` | Horizontal bar chart |
| `frontend/src/features/people/components/MethodBreakdown.tsx` | Grouped bar chart |

### Modified Frontend Files

| File | Change |
|------|--------|
| `frontend/package.json` | Add `react-plotly.js`, `plotly.js-dist-min`; remove `recharts` |
| `frontend/src/App.tsx` | Add 3 new routes |
| `frontend/src/layouts/AppLayout.tsx` | Add "Optimize" nav item in Core group |
| `frontend/src/features/brews/components/BrewWizard.tsx` | Add suggestion state + link-on-save logic |
| `frontend/src/features/brews/components/BrewStepParams.tsx` | Accept suggestion prop, show highlighted fields + info banner |
| `frontend/src/features/people/PeoplePage.tsx` | Row click → navigate to preferences |
| `frontend/src/features/dashboard/DashboardPage.tsx` | Add optimization summary card |
| `frontend/src/components/TasteRadar.tsx` | Migrate from Recharts to Plotly |

---

## Phase A: Backend

### Task 1: Response Schemas for Posterior & Feature Importance

**Files:**
- Modify: `src/beanbay/schemas/optimization.py` (append after line 532)

- [ ] **Step 1: Add new schemas**

Append to the end of `src/beanbay/schemas/optimization.py`:

```python
# ---------------------------------------------------------------------------
# Posterior Predictions
# ---------------------------------------------------------------------------


class MeasurementPoint(SQLModel):
    """A single measurement for overlay on posterior plots.

    Attributes
    ----------
    values : dict
        Parameter values for this measurement.
    score : float
        Observed taste score.
    """

    values: dict
    score: float


class PosteriorResponse(SQLModel):
    """Response from the posterior predictions endpoint.

    Attributes
    ----------
    params : list[str]
        Parameter names that were swept.
    grid : list[list[float]]
        Grid values per parameter (one array per param).
    mean : list
        Predicted mean scores (1D for single param, 2D nested for two).
    std : list
        Predicted std (same shape as mean).
    measurements : list[MeasurementPoint]
        Actual measurements for chart overlay.
    """

    params: list[str]
    grid: list[list[float]]
    mean: list
    std: list
    measurements: list[MeasurementPoint] = []


# ---------------------------------------------------------------------------
# Feature Importance
# ---------------------------------------------------------------------------


class FeatureImportanceResponse(SQLModel):
    """Response from the feature importance endpoint.

    Attributes
    ----------
    parameters : list[str]
        Parameter names sorted by importance descending.
    importance : list[float]
        SHAP importance values (same order as parameters).
    measurement_count : int
        Number of measurements used for the analysis.
    """

    parameters: list[str]
    importance: list[float]
    measurement_count: int
```

- [ ] **Step 2: Verify import**

Run: `uv run python -c "from beanbay.schemas.optimization import PosteriorResponse, FeatureImportanceResponse, MeasurementPoint; print('OK')"`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add src/beanbay/schemas/optimization.py
git commit -m "feat(schemas): add PosteriorResponse and FeatureImportanceResponse"
```

---

### Task 2: Posterior Predictions Endpoint

**Files:**
- Modify: `src/beanbay/routers/optimize.py` (add import + endpoint after progress section ~line 571)
- Test: `tests/integration/test_optimize_api.py`

- [ ] **Step 1: Write failing tests**

Add a helper and test class to `tests/integration/test_optimize_api.py`. The helper sets up a campaign with a trained BayBE model by creating brews, building a BayBE campaign, adding measurements, and storing the serialized state.

Add these imports at the top of the file (alongside existing imports):

```python
import pandas as pd
from baybe import Campaign as BaybeCampaign
from beanbay.models.optimization import (
    BeanParameterOverride,
    Campaign,
    MethodParameterDefault,
)
from beanbay.services.optimizer import OptimizerService
from beanbay.services.parameter_ranges import compute_effective_ranges
```

Add helper after the existing `_create_brew_with_taste` function (~line 781):

```python
POSTERIOR = "/api/v1/optimize/campaigns/{campaign_id}/posterior"
IMPORTANCE = "/api/v1/optimize/campaigns/{campaign_id}/feature-importance"


def _setup_trained_campaign(client, session, measurement_count=3):
    """Create a campaign with a trained BayBE model and measurements.

    Seeds brew methods/defaults, creates a pour-over campaign, adds
    ``measurement_count`` brews with taste scores, builds and trains a
    BayBE campaign, and stores the serialized state on the campaign row.

    Returns
    -------
    dict
        Keys: campaign_id, bean_id, brew_setup_id, param_names.
    """
    seed_brew_methods(session)
    session.commit()
    seed_method_parameter_defaults(session)
    session.commit()

    pour_over = session.exec(
        select(BrewMethod).where(BrewMethod.name == "pour-over")
    ).one()

    bean_id = _create_bean(client, f"Posterior Bean {measurement_count}")
    setup_id = _create_brew_setup(client, pour_over.id)
    person_id = _create_person(client, "Posterior Tester")
    bag_id = _create_bag(client, bean_id)

    # Create campaign via API
    resp = client.post(
        CAMPAIGNS,
        json={"bean_id": bean_id, "brew_setup_id": setup_id},
    )
    assert resp.status_code == 201
    campaign_id = resp.json()["id"]

    # Create brews with taste scores
    for i in range(measurement_count):
        _create_brew_with_taste(
            client, bag_id, setup_id, person_id, score=6.0 + i * 0.5,
        )

    # Load campaign row and effective ranges
    campaign_row = session.get(Campaign, uuid.UUID(campaign_id))
    defaults = session.exec(
        select(MethodParameterDefault).where(
            MethodParameterDefault.brew_method_id == pour_over.id
        )
    ).all()
    effective_ranges = compute_effective_ranges(
        list(defaults), None, None, []
    )
    param_names = [r.parameter_name for r in effective_ranges]

    # Build BayBE campaign and train with measurements
    baybe_campaign = OptimizerService.build_campaign(effective_ranges)

    from beanbay.models.bean import Bag
    from beanbay.models.brew import Brew, BrewTaste

    stmt = (
        select(Brew)
        .join(Bag, Brew.bag_id == Bag.id)
        .join(BrewTaste, Brew.id == BrewTaste.brew_id)
        .where(
            Bag.bean_id == uuid.UUID(bean_id),
            Brew.brew_setup_id == uuid.UUID(setup_id),
            Brew.is_failed == False,  # noqa: E712
            Brew.retired_at.is_(None),
            BrewTaste.score.is_not(None),
        )
    )
    brews = session.exec(stmt).all()

    rows = []
    for brew in brews:
        row = {}
        for pname in param_names:
            row[pname] = getattr(brew, pname, None)
        row["score"] = brew.taste.score
        rows.append(row)

    measurements_df = pd.DataFrame(rows).dropna(subset=param_names)
    baybe_campaign.add_measurements(measurements_df)

    # Store trained state
    campaign_row.campaign_json = baybe_campaign.to_json()
    campaign_row.measurement_count = len(measurements_df)
    campaign_row.best_score = float(measurements_df["score"].max())
    campaign_row.phase = OptimizerService.determine_phase(len(measurements_df))
    bounds_fp, param_fp = OptimizerService.compute_fingerprints(
        effective_ranges
    )
    campaign_row.bounds_fingerprint = bounds_fp
    campaign_row.param_fingerprint = param_fp
    session.add(campaign_row)
    session.commit()

    return {
        "campaign_id": campaign_id,
        "bean_id": bean_id,
        "brew_setup_id": setup_id,
        "param_names": param_names,
    }
```

Add test class:

```python
class TestPosteriorPredictions:
    """Tests for GET /optimize/campaigns/{id}/posterior."""

    def test_posterior_1d(self, recommend_client, recommend_session):
        """1D posterior returns grid, mean, std arrays of correct length."""
        ids = _setup_trained_campaign(
            recommend_client, recommend_session, measurement_count=3
        )
        resp = recommend_client.get(
            POSTERIOR.format(campaign_id=ids["campaign_id"]),
            params={"params": "temperature", "points": 10},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["params"] == ["temperature"]
        assert len(body["grid"]) == 1
        assert len(body["grid"][0]) == 10
        assert len(body["mean"]) == 10
        assert len(body["std"]) == 10
        assert all(isinstance(v, (int, float)) for v in body["mean"])
        assert all(isinstance(v, (int, float)) for v in body["std"])

    def test_posterior_2d(self, recommend_client, recommend_session):
        """2D posterior returns nested arrays (points x points)."""
        ids = _setup_trained_campaign(
            recommend_client, recommend_session, measurement_count=3
        )
        resp = recommend_client.get(
            POSTERIOR.format(campaign_id=ids["campaign_id"]),
            params={"params": "temperature,dose", "points": 5},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["params"] == ["temperature", "dose"]
        assert len(body["grid"]) == 2
        # 2D: mean is a nested array (rows x cols)
        assert len(body["mean"]) == 5
        assert len(body["mean"][0]) == 5

    def test_posterior_includes_measurements(
        self, recommend_client, recommend_session
    ):
        """Posterior response includes actual measurement overlay data."""
        ids = _setup_trained_campaign(
            recommend_client, recommend_session, measurement_count=3
        )
        resp = recommend_client.get(
            POSTERIOR.format(campaign_id=ids["campaign_id"]),
            params={"params": "temperature"},
        )
        body = resp.json()
        assert len(body["measurements"]) >= 1
        m = body["measurements"][0]
        assert "values" in m
        assert "score" in m

    def test_posterior_insufficient_data(
        self, recommend_client, recommend_session
    ):
        """Returns 422 when campaign has < 2 valid measurements."""
        ids = _setup_trained_campaign(
            recommend_client, recommend_session, measurement_count=1
        )
        resp = recommend_client.get(
            POSTERIOR.format(campaign_id=ids["campaign_id"]),
            params={"params": "temperature"},
        )
        assert resp.status_code == 422

    def test_posterior_campaign_not_found(self, recommend_client):
        """Returns 404 for non-existent campaign."""
        fake_id = str(uuid.uuid4())
        resp = recommend_client.get(
            POSTERIOR.format(campaign_id=fake_id),
            params={"params": "temperature"},
        )
        assert resp.status_code == 404

    def test_posterior_invalid_param_name(
        self, recommend_client, recommend_session
    ):
        """Returns 422 for unknown parameter name."""
        ids = _setup_trained_campaign(
            recommend_client, recommend_session, measurement_count=3
        )
        resp = recommend_client.get(
            POSTERIOR.format(campaign_id=ids["campaign_id"]),
            params={"params": "nonexistent_param"},
        )
        assert resp.status_code == 422
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/integration/test_optimize_api.py::TestPosteriorPredictions -v --no-header -x`

Expected: FAIL (endpoint not implemented)

- [ ] **Step 3: Implement the endpoint**

Add import to `src/beanbay/routers/optimize.py` (line 26 area, add to the schema imports):

```python
from beanbay.schemas.optimization import (
    # ... existing imports ...
    FeatureImportanceResponse,
    MeasurementPoint,
    PosteriorResponse,
)
```

Add the endpoint after the progress section (~after line 571, before the Method Parameter Defaults section):

```python
# ======================================================================
# Posterior Predictions
# ======================================================================


@router.get(
    "/optimize/campaigns/{campaign_id}/posterior",
    response_model=PosteriorResponse,
)
def get_posterior(
    campaign_id: uuid.UUID,
    session: SessionDep,
    params: str = Query(
        ..., description="Comma-separated parameter names (1 or 2)"
    ),
    points: int = Query(30, ge=5, le=100),
) -> PosteriorResponse:
    """Get posterior mean/std predictions over a parameter grid.

    Builds a grid across the requested parameter(s), holding all other
    parameters at their best-known values (highest-scoring measurement).
    Calls ``campaign.posterior_stats()`` for mean and std at each point.

    Parameters
    ----------
    campaign_id : uuid.UUID
        Primary key of the campaign.
    session : SessionDep
        Database session.
    params : str
        Comma-separated parameter names (1 or 2).
    points : int
        Grid resolution per dimension (5–100, default 30).

    Returns
    -------
    PosteriorResponse
        Grid coordinates, predicted mean/std, and measurement overlay.

    Raises
    ------
    HTTPException
        404 if campaign not found, 422 if insufficient data or invalid
        parameter names.
    """
    import numpy as np
    import pandas as pd
    from baybe import Campaign as BaybeCampaign

    campaign = session.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found.")
    if not campaign.campaign_json:
        raise HTTPException(
            status_code=422, detail="No trained model yet."
        )

    # Parse and validate requested params
    param_names = [p.strip() for p in params.split(",")]
    if len(param_names) not in (1, 2):
        raise HTTPException(
            status_code=422,
            detail="Provide 1 or 2 comma-separated parameter names.",
        )

    effective_ranges = _compute_campaign_ranges(session, campaign)
    range_map = {r.parameter_name: r for r in effective_ranges}
    all_range_names = [r.parameter_name for r in effective_ranges]

    for pname in param_names:
        r = range_map.get(pname)
        if r is None:
            raise HTTPException(
                status_code=422, detail=f"Unknown parameter: {pname}"
            )
        if r.allowed_values is not None:
            raise HTTPException(
                status_code=422,
                detail=f"Cannot sweep categorical parameter: {pname}",
            )

    # Load measurements
    stmt = (
        select(Brew)
        .join(Bag, Brew.bag_id == Bag.id)
        .join(BrewTaste, Brew.id == BrewTaste.brew_id)
        .where(
            Bag.bean_id == campaign.bean_id,
            Brew.brew_setup_id == campaign.brew_setup_id,
            Brew.is_failed == False,  # noqa: E712
            Brew.retired_at.is_(None),
            BrewTaste.score.is_not(None),
        )
    )
    brews = session.exec(stmt).all()

    meas_rows: list[dict] = []
    meas_points: list[MeasurementPoint] = []
    for brew in brews:
        row: dict = {}
        vals: dict = {}
        for pname in all_range_names:
            v = getattr(brew, pname, None)
            row[pname] = v
            vals[pname] = v
        row["score"] = brew.taste.score
        meas_rows.append(row)
        meas_points.append(
            MeasurementPoint(values=vals, score=brew.taste.score)
        )

    if meas_rows:
        meas_df = pd.DataFrame(meas_rows).dropna(subset=all_range_names)
    else:
        meas_df = pd.DataFrame()

    if len(meas_df) < 2:
        raise HTTPException(
            status_code=422,
            detail=f"Need >= 2 valid measurements (have {len(meas_df)}).",
        )

    # Best-known values from highest-scoring measurement
    best_idx = meas_df["score"].idxmax()
    best_row = meas_df.iloc[best_idx]

    # Build grid arrays
    grid_arrays: list[list[float]] = []
    for pname in param_names:
        r = range_map[pname]
        grid_arrays.append(
            np.linspace(r.min_value, r.max_value, points).tolist()
        )

    # Build grid DataFrame
    if len(param_names) == 1:
        grid_df = pd.DataFrame({param_names[0]: grid_arrays[0]})
    else:
        xs, ys = np.meshgrid(grid_arrays[0], grid_arrays[1])
        grid_df = pd.DataFrame(
            {param_names[0]: xs.flatten(), param_names[1]: ys.flatten()}
        )

    # Fill non-swept parameters with best-known values
    for er in effective_ranges:
        if er.parameter_name not in param_names:
            if er.allowed_values is not None:
                fallback = er.allowed_values.split(",")[0].strip()
            else:
                fallback = (er.min_value + er.max_value) / 2
            grid_df[er.parameter_name] = best_row.get(
                er.parameter_name, fallback
            )

    # Posterior predictions
    baybe_campaign = BaybeCampaign.from_json(campaign.campaign_json)
    stats = baybe_campaign.posterior_stats(grid_df)

    mean_arr = stats["score_Mean"].values
    std_arr = stats["score_Std"].values

    if len(param_names) == 2:
        mean_out: list = mean_arr.reshape(points, points).tolist()
        std_out: list = std_arr.reshape(points, points).tolist()
    else:
        mean_out = mean_arr.tolist()
        std_out = std_arr.tolist()

    return PosteriorResponse(
        params=param_names,
        grid=grid_arrays,
        mean=mean_out,
        std=std_out,
        measurements=meas_points,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/integration/test_optimize_api.py::TestPosteriorPredictions -v --no-header`

Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/beanbay/routers/optimize.py src/beanbay/schemas/optimization.py tests/integration/test_optimize_api.py
git commit -m "feat(api): add posterior predictions endpoint for campaign visualizations"
```

---

### Task 3: Feature Importance Endpoint

**Files:**
- Modify: `src/beanbay/routers/optimize.py` (add endpoint after posterior section)
- Test: `tests/integration/test_optimize_api.py`

- [ ] **Step 1: Write failing tests**

Add test class to `tests/integration/test_optimize_api.py`:

```python
class TestFeatureImportance:
    """Tests for GET /optimize/campaigns/{id}/feature-importance."""

    def test_feature_importance_with_enough_data(
        self, recommend_client, recommend_session
    ):
        """Returns sorted parameter importance with >= 3 measurements."""
        ids = _setup_trained_campaign(
            recommend_client, recommend_session, measurement_count=4
        )
        resp = recommend_client.get(
            IMPORTANCE.format(campaign_id=ids["campaign_id"])
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["parameters"]) > 0
        assert len(body["importance"]) == len(body["parameters"])
        assert body["measurement_count"] == 4
        # Verify sorted descending
        for i in range(len(body["importance"]) - 1):
            assert body["importance"][i] >= body["importance"][i + 1]

    def test_feature_importance_insufficient_data(
        self, recommend_client, recommend_session
    ):
        """Returns 422 when campaign has < 3 measurements."""
        ids = _setup_trained_campaign(
            recommend_client, recommend_session, measurement_count=2
        )
        resp = recommend_client.get(
            IMPORTANCE.format(campaign_id=ids["campaign_id"])
        )
        assert resp.status_code == 422

    def test_feature_importance_not_found(self, recommend_client):
        """Returns 404 for non-existent campaign."""
        fake_id = str(uuid.uuid4())
        resp = recommend_client.get(
            IMPORTANCE.format(campaign_id=fake_id)
        )
        assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/integration/test_optimize_api.py::TestFeatureImportance -v --no-header -x`

Expected: FAIL (endpoint not implemented)

- [ ] **Step 3: Implement the endpoint**

Add to `src/beanbay/routers/optimize.py` after the posterior endpoint:

```python
# ======================================================================
# Feature Importance (SHAP)
# ======================================================================


@router.get(
    "/optimize/campaigns/{campaign_id}/feature-importance",
    response_model=FeatureImportanceResponse,
)
def get_feature_importance(
    campaign_id: uuid.UUID,
    session: SessionDep,
) -> FeatureImportanceResponse:
    """Get SHAP-based feature importance for a campaign.

    Uses ``SHAPInsight.from_campaign()`` to compute per-parameter
    importance scores. Requires at least 3 valid measurements.

    Parameters
    ----------
    campaign_id : uuid.UUID
        Primary key of the campaign.
    session : SessionDep
        Database session.

    Returns
    -------
    FeatureImportanceResponse
        Parameters sorted by importance descending with SHAP values.

    Raises
    ------
    HTTPException
        404 if campaign not found, 422 if insufficient data.
    """
    import numpy as np
    from baybe import Campaign as BaybeCampaign
    from baybe.insights.shap import SHAPInsight

    campaign = session.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found.")
    if not campaign.campaign_json:
        raise HTTPException(
            status_code=422, detail="No trained model yet."
        )
    if campaign.measurement_count < 3:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Need >= 3 measurements for SHAP analysis "
                f"(have {campaign.measurement_count})."
            ),
        )

    baybe_campaign = BaybeCampaign.from_json(campaign.campaign_json)
    insight = SHAPInsight.from_campaign(baybe_campaign)

    # Extract per-feature importance from SHAP explanation
    explanation = insight.explanation
    importance = np.abs(explanation.values).mean(axis=0).tolist()
    feature_names = list(explanation.feature_names)

    # Sort by importance descending
    pairs = sorted(
        zip(feature_names, importance), key=lambda x: x[1], reverse=True
    )
    sorted_names = [p[0] for p in pairs]
    sorted_importance = [round(p[1], 6) for p in pairs]

    return FeatureImportanceResponse(
        parameters=sorted_names,
        importance=sorted_importance,
        measurement_count=campaign.measurement_count,
    )
```

> **Note for executor:** The `SHAPInsight` import path may be `from baybe.insights.shap import SHAPInsight` or `from baybe.insights import SHAPInsight`. Check with `uv run python -c "from baybe.insights.shap import SHAPInsight; print('OK')"` and adjust if needed. Similarly, `insight.explanation` may be `insight.shap_values` or similar — verify with `dir(insight)` at runtime and adapt the attribute access.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/integration/test_optimize_api.py::TestFeatureImportance -v --no-header`

Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/beanbay/routers/optimize.py tests/integration/test_optimize_api.py
git commit -m "feat(api): add SHAP feature importance endpoint for campaigns"
```

---

### Task 4: Taskiq Worker Fix — Populate predicted_score/predicted_std

**Files:**
- Modify: `src/beanbay/services/taskiq_broker.py` (~after line 166, before campaign update)
- Test: `tests/integration/test_optimize_api.py`

- [ ] **Step 1: Write failing test**

Add test class to `tests/integration/test_optimize_api.py`:

```python
class TestPredictedScorePopulation:
    """Verify taskiq worker populates predicted_score/predicted_std."""

    def test_recommendation_has_predicted_score_with_measurements(
        self, recommend_client, recommend_session
    ):
        """After recommend with 2+ measurements, predicted_score is set."""
        ids = _setup_campaign(recommend_client, recommend_session)
        person_id = _create_person(recommend_client, "Scorer")
        bag_id = _create_bag(recommend_client, ids["bean_id"])

        # Create 3 brews with taste scores
        for score in [6.0, 7.0, 8.0]:
            _create_brew_with_taste(
                recommend_client,
                bag_id,
                ids["brew_setup_id"],
                person_id,
                score=score,
            )

        # Request recommendation (InMemoryBroker runs inline)
        resp = recommend_client.post(
            RECOMMEND.format(campaign_id=ids["campaign_id"])
        )
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]

        # Get job result
        job_resp = recommend_client.get(f"{JOBS}/{job_id}")
        assert job_resp.json()["status"] == "completed"
        result_id = job_resp.json()["result_id"]

        # Get recommendation detail
        rec_resp = recommend_client.get(f"{RECOMMENDATIONS}/{result_id}")
        assert rec_resp.status_code == 200
        rec = rec_resp.json()
        assert rec["predicted_score"] is not None
        assert rec["predicted_std"] is not None
        assert isinstance(rec["predicted_score"], (int, float))
        assert isinstance(rec["predicted_std"], (int, float))
        assert rec["predicted_std"] >= 0

    def test_recommendation_no_predicted_score_without_measurements(
        self, recommend_client, recommend_session
    ):
        """Recommendation with 0 measurements has null predicted_score."""
        ids = _setup_campaign(recommend_client, recommend_session)

        resp = recommend_client.post(
            RECOMMEND.format(campaign_id=ids["campaign_id"])
        )
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]

        job_resp = recommend_client.get(f"{JOBS}/{job_id}")
        assert job_resp.json()["status"] == "completed"
        result_id = job_resp.json()["result_id"]

        rec_resp = recommend_client.get(f"{RECOMMENDATIONS}/{result_id}")
        rec = rec_resp.json()
        # With 0 measurements, predicted_score should be null
        assert rec["predicted_score"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/integration/test_optimize_api.py::TestPredictedScorePopulation -v --no-header -x`

Expected: First test FAILS (`predicted_score` is `None`)

- [ ] **Step 3: Add predicted score population to taskiq worker**

In `src/beanbay/services/taskiq_broker.py`, add after line 166 (`session.flush()`) and before line 169 (`# 14. Update campaign state`):

```python
            # 13b. Populate predicted score/std if model is trained
            if valid_count >= 2:
                try:
                    rec_df = pd.DataFrame([rounded_values])
                    # Ensure all search space columns are present
                    for pname in param_names:
                        if pname not in rec_df.columns:
                            rec_df[pname] = rounded_values.get(pname)
                    posterior = baybe_campaign.posterior_stats(rec_df)
                    rec.predicted_score = round(
                        float(posterior["score_Mean"].iloc[0]), 4
                    )
                    rec.predicted_std = round(
                        float(posterior["score_Std"].iloc[0]), 4
                    )
                except Exception:
                    logger.warning(
                        "Could not compute posterior stats for rec %s",
                        rec.id,
                    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/integration/test_optimize_api.py::TestPredictedScorePopulation -v --no-header`

Expected: Both tests PASS

- [ ] **Step 5: Run full test suite to verify no regressions**

Run: `uv run pytest tests/integration/test_optimize_api.py -v --no-header`

Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/beanbay/services/taskiq_broker.py tests/integration/test_optimize_api.py
git commit -m "fix(worker): populate predicted_score and predicted_std on recommendations"
```

---

## Phase B: Frontend Infrastructure

### Task 5: Install Plotly & Create PlotlyChart Wrapper

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/src/components/PlotlyChart.tsx`

- [ ] **Step 1: Install Plotly packages**

```bash
cd frontend && bun add react-plotly.js plotly.js-dist-min && cd ..
```

> **Note:** Do NOT remove `recharts` yet — `TasteRadar.tsx` still depends on it. Recharts removal happens in Task 18 alongside the TasteRadar migration.

- [ ] **Step 2: Add Plotly type declarations**

Add to `frontend/src/vite-env.d.ts` (or create a new `frontend/src/plotly.d.ts`):

```typescript
declare module 'react-plotly.js' {
  import { Component } from 'react';
  import type Plotly from 'plotly.js-dist-min';

  interface PlotParams {
    data: Plotly.Data[];
    layout?: Partial<Plotly.Layout>;
    config?: Partial<Plotly.Config>;
    style?: React.CSSProperties;
    useResizeHandler?: boolean;
    onInitialized?: (figure: { data: Plotly.Data[]; layout: Partial<Plotly.Layout> }, graphDiv: HTMLElement) => void;
    onUpdate?: (figure: { data: Plotly.Data[]; layout: Partial<Plotly.Layout> }, graphDiv: HTMLElement) => void;
  }

  export default class Plot extends Component<PlotParams> {}
}

declare module 'plotly.js-dist-min' {
  import type Plotly from 'plotly.js';
  export = Plotly;
}
```

- [ ] **Step 3: Create PlotlyChart wrapper**

Create `frontend/src/components/PlotlyChart.tsx`:

```typescript
import { useTheme } from '@mui/material';
import Plot from 'react-plotly.js';
import type Plotly from 'plotly.js-dist-min';

interface PlotlyChartProps {
  data: Plotly.Data[];
  layout?: Partial<Plotly.Layout>;
  style?: React.CSSProperties;
  config?: Partial<Plotly.Config>;
}

export default function PlotlyChart({
  data,
  layout = {},
  style,
  config,
}: PlotlyChartProps) {
  const theme = useTheme();

  const themedLayout: Partial<Plotly.Layout> = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: {
      color: theme.palette.text.primary,
      family: theme.typography.fontFamily as string,
    },
    xaxis: {
      gridcolor: theme.palette.divider,
      zerolinecolor: theme.palette.divider,
      ...layout.xaxis,
    },
    yaxis: {
      gridcolor: theme.palette.divider,
      zerolinecolor: theme.palette.divider,
      ...layout.yaxis,
    },
    margin: { t: 40, r: 20, b: 50, l: 55 },
    ...layout,
  };

  const defaultConfig: Partial<Plotly.Config> = {
    displayModeBar: false,
    responsive: true,
    ...config,
  };

  return (
    <Plot
      data={data}
      layout={themedLayout}
      config={defaultConfig}
      style={{ width: '100%', height: '100%', ...style }}
      useResizeHandler
    />
  );
}
```

- [ ] **Step 4: Verify build**

Run: `cd frontend && bun run build && cd ..`

Expected: Build succeeds without errors

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/bun.lock frontend/src/components/PlotlyChart.tsx frontend/src/vite-env.d.ts
git commit -m "feat(frontend): add Plotly wrapper component with react-plotly.js"
```

---

### Task 6: Optimization API Hooks

**Files:**
- Create: `frontend/src/features/optimize/hooks.ts`

- [ ] **Step 1: Create hooks file**

Create `frontend/src/features/optimize/hooks.ts`:

```typescript
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CampaignListItem {
  id: string;
  bean_name: string | null;
  brew_setup_name: string | null;
  phase: string;
  measurement_count: number;
  best_score: number | null;
  created_at: string;
}

export interface EffectiveRange {
  parameter_name: string;
  min_value: number | null;
  max_value: number | null;
  step: number | null;
  allowed_values: string | null;
  source: string;
}

export interface CampaignDetail extends CampaignListItem {
  bean_id: string;
  brew_setup_id: string;
  updated_at: string;
  effective_ranges: EffectiveRange[];
}

export interface ScoreHistoryEntry {
  shot_number: number;
  score: number | null;
  is_failed: boolean;
  phase: string | null;
}

export interface CampaignProgress {
  phase: string;
  measurement_count: number;
  best_score: number | null;
  convergence: { status: string; improvement_rate: number | null };
  score_history: ScoreHistoryEntry[];
}

export interface PosteriorData {
  params: string[];
  grid: number[][];
  mean: number[] | number[][];
  std: number[] | number[][];
  measurements: { values: Record<string, number>; score: number }[];
}

export interface FeatureImportanceData {
  parameters: string[];
  importance: number[];
  measurement_count: number;
}

export interface Recommendation {
  id: string;
  campaign_id: string;
  brew_id: string | null;
  phase: string;
  predicted_score: number | null;
  predicted_std: number | null;
  parameter_values: Record<string, number | string>;
  status: string;
  created_at: string;
}

export interface PersonPreferences {
  person: { id: string; name: string };
  brew_stats: {
    total_brews: number;
    avg_score: number | null;
    favorite_method: string | null;
  };
  top_beans: { bean_id: string; name: string; avg_score: number; brew_count: number }[];
  flavor_profile: { tag: string; frequency: number }[];
  roast_preference: Record<string, number>;
  origin_preferences: { origin: string; avg_score: number; brew_count: number }[];
  method_breakdown: { method: string; brew_count: number; avg_score: number }[];
}

// ---------------------------------------------------------------------------
// Query Hooks
// ---------------------------------------------------------------------------

export function useCampaigns() {
  return useQuery<CampaignListItem[]>({
    queryKey: ['campaigns'],
    queryFn: async () => {
      const { data } = await apiClient.get('/optimize/campaigns');
      return data;
    },
  });
}

export function useCampaignDetail(campaignId: string) {
  return useQuery<CampaignDetail>({
    queryKey: ['campaigns', campaignId],
    queryFn: async () => {
      const { data } = await apiClient.get(`/optimize/campaigns/${campaignId}`);
      return data;
    },
    enabled: !!campaignId,
  });
}

export function useCampaignProgress(campaignId: string) {
  return useQuery<CampaignProgress>({
    queryKey: ['campaigns', campaignId, 'progress'],
    queryFn: async () => {
      const { data } = await apiClient.get(
        `/optimize/campaigns/${campaignId}/progress`,
      );
      return data;
    },
    enabled: !!campaignId,
  });
}

export function usePosterior(
  campaignId: string,
  params: string,
  points?: number,
) {
  return useQuery<PosteriorData>({
    queryKey: ['campaigns', campaignId, 'posterior', params, points],
    queryFn: async () => {
      const { data } = await apiClient.get(
        `/optimize/campaigns/${campaignId}/posterior`,
        { params: { params, points } },
      );
      return data;
    },
    enabled: !!campaignId && !!params,
    retry: false,
  });
}

export function useFeatureImportance(campaignId: string) {
  return useQuery<FeatureImportanceData>({
    queryKey: ['campaigns', campaignId, 'feature-importance'],
    queryFn: async () => {
      const { data } = await apiClient.get(
        `/optimize/campaigns/${campaignId}/feature-importance`,
      );
      return data;
    },
    enabled: !!campaignId,
    retry: false,
  });
}

export function useCampaignRecommendations(campaignId: string) {
  return useQuery<Recommendation[]>({
    queryKey: ['campaigns', campaignId, 'recommendations'],
    queryFn: async () => {
      const { data } = await apiClient.get(
        `/optimize/campaigns/${campaignId}/recommendations`,
      );
      return data;
    },
    enabled: !!campaignId,
  });
}

export function usePersonPreferences(personId: string) {
  return useQuery<PersonPreferences>({
    queryKey: ['people', personId, 'preferences'],
    queryFn: async () => {
      const { data } = await apiClient.get(
        `/optimize/people/${personId}/preferences`,
      );
      return data;
    },
    enabled: !!personId,
  });
}

// ---------------------------------------------------------------------------
// Mutation Hooks
// ---------------------------------------------------------------------------

/** Full suggest flow: create campaign → request recommendation → poll → return result. */
export function useSuggest() {
  return useMutation({
    mutationFn: async ({
      beanId,
      brewSetupId,
    }: {
      beanId: string;
      brewSetupId: string;
    }) => {
      // 1. Create or get existing campaign
      const { data: campaign } = await apiClient.post('/optimize/campaigns', {
        bean_id: beanId,
        brew_setup_id: brewSetupId,
      });

      // 2. Request recommendation
      const { data: jobData } = await apiClient.post(
        `/optimize/campaigns/${campaign.id}/recommend`,
      );

      // 3. Poll job until complete
      let job = jobData;
      while (job.status === 'pending' || job.status === 'running') {
        await new Promise((r) => setTimeout(r, 500));
        const { data } = await apiClient.get(
          `/optimize/jobs/${job.job_id}`,
        );
        job = data;
      }

      if (job.status === 'failed') {
        throw new Error(job.error_message || 'Recommendation failed');
      }

      // 4. Get recommendation details
      const { data: rec } = await apiClient.get(
        `/optimize/recommendations/${job.result_id}`,
      );

      return {
        recommendation: rec as Recommendation,
        campaignId: campaign.id as string,
      };
    },
  });
}

export function useLinkRecommendation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      recommendationId,
      brewId,
    }: {
      recommendationId: string;
      brewId: string;
    }) => {
      const { data } = await apiClient.post(
        `/optimize/recommendations/${recommendationId}/link`,
        { brew_id: brewId },
      );
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && bun run build && cd ..`

Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/optimize/hooks.ts
git commit -m "feat(frontend): add React Query hooks for optimization endpoints"
```

---

### Task 7: Routes & Navigation

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/layouts/AppLayout.tsx`

- [ ] **Step 1: Add lazy imports and routes to App.tsx**

In `frontend/src/App.tsx`, add lazy imports (alongside existing lazy imports):

```typescript
const CampaignListPage = lazy(() => import('@/features/optimize/pages/CampaignListPage'));
const CampaignDetailPage = lazy(() => import('@/features/optimize/pages/CampaignDetailPage'));
const PersonPreferencesPage = lazy(() => import('@/features/people/pages/PersonPreferencesPage'));
```

Add routes inside the `<Route element={<AppLayout />}>` block, before the closing `</Route>`:

```tsx
<Route path="/optimize" element={<CampaignListPage />} />
<Route path="/optimize/:campaignId" element={<CampaignDetailPage />} />
<Route path="/people/:personId/preferences" element={<PersonPreferencesPage />} />
```

- [ ] **Step 2: Add navigation item to AppLayout.tsx**

In `frontend/src/layouts/AppLayout.tsx`:

Add import at top:
```typescript
import TuneIcon from '@mui/icons-material/Tune';
```

> **Note:** `Tune` is already imported as `SetupsIcon`. Use a different icon. Add: `import AutoFixHigh as OptimizeIcon from '@mui/icons-material/AutoFixHigh';`

In the `navGroups` array, add to the "Core" group (after Brews):

```typescript
{ label: 'Optimize', path: '/optimize', icon: <OptimizeIcon /> },
```

- [ ] **Step 3: Create placeholder pages**

Create minimal placeholder pages so the build passes. These will be fully implemented in later tasks.

`frontend/src/features/optimize/pages/CampaignListPage.tsx`:
```typescript
import { Typography } from '@mui/material';
export default function CampaignListPage() {
  return <Typography variant="h5">Campaigns</Typography>;
}
```

`frontend/src/features/optimize/pages/CampaignDetailPage.tsx`:
```typescript
import { Typography } from '@mui/material';
export default function CampaignDetailPage() {
  return <Typography variant="h5">Campaign Detail</Typography>;
}
```

`frontend/src/features/people/pages/PersonPreferencesPage.tsx`:
```typescript
import { Typography } from '@mui/material';
export default function PersonPreferencesPage() {
  return <Typography variant="h5">Preferences</Typography>;
}
```

- [ ] **Step 4: Verify build and dev server**

Run: `cd frontend && bun run build && cd ..`

Expected: Build succeeds. Routes `/optimize`, `/optimize/:id`, `/people/:id/preferences` render placeholders.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx frontend/src/layouts/AppLayout.tsx frontend/src/features/optimize/pages/ frontend/src/features/people/pages/
git commit -m "feat(frontend): add optimization routes, navigation item, and placeholder pages"
```

---

## Phase C: Campaign Pages

### Task 8: Campaign List Page

**Files:**
- Modify: `frontend/src/features/optimize/pages/CampaignListPage.tsx` (replace placeholder)

- [ ] **Step 1: Implement CampaignListPage**

Replace `frontend/src/features/optimize/pages/CampaignListPage.tsx`:

```typescript
import { useNavigate } from 'react-router';
import {
  Box, Card, CardActionArea, CardContent, Chip, Grid, LinearProgress,
  Typography, Tooltip,
} from '@mui/material';
import PageHeader from '@/components/PageHeader';
import EmptyState from '@/components/EmptyState';
import { useCampaigns } from '../hooks';

const phaseColor: Record<string, 'info' | 'warning' | 'success'> = {
  random: 'info',
  learning: 'warning',
  optimizing: 'success',
};

function scoreColor(score: number | null): string {
  if (score == null) return 'text.secondary';
  if (score >= 8) return 'success.main';
  if (score >= 6) return 'warning.main';
  return 'error.main';
}

export default function CampaignListPage() {
  const navigate = useNavigate();
  const { data: campaigns, isLoading } = useCampaigns();

  return (
    <Box>
      <PageHeader title="Optimization Campaigns" />

      {isLoading && <LinearProgress />}

      {!isLoading && (!campaigns || campaigns.length === 0) && (
        <EmptyState
          title="No campaigns yet"
          description="Campaigns are created automatically when you use the Suggest button in the Brew Wizard."
        />
      )}

      <Grid container spacing={2}>
        {campaigns?.map((c) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={c.id}>
            <Card variant="outlined">
              <CardActionArea onClick={() => navigate(`/optimize/${c.id}`)}>
                <CardContent>
                  <Typography variant="subtitle1" fontWeight="bold" noWrap>
                    {c.bean_name ?? 'Unknown bean'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" noWrap>
                    {c.brew_setup_name ?? 'Unknown setup'}
                  </Typography>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1.5 }}>
                    <Chip
                      label={c.phase}
                      size="small"
                      color={phaseColor[c.phase] ?? 'default'}
                    />
                    <Typography variant="body2" color="text.secondary">
                      {c.measurement_count} shots
                    </Typography>
                  </Box>

                  {c.best_score != null && (
                    <Typography
                      variant="h5"
                      fontWeight="bold"
                      sx={{ mt: 1, color: scoreColor(c.best_score) }}
                    >
                      {c.best_score.toFixed(1)}
                    </Typography>
                  )}

                  {/* Convergence progress bar */}
                  <Tooltip title={`${c.phase} phase — ${c.measurement_count} measurements`}>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min(100, (c.measurement_count / 15) * 100)}
                      sx={{ mt: 1.5, height: 6, borderRadius: 3 }}
                      color={c.phase === 'optimizing' ? 'success' : c.phase === 'learning' ? 'warning' : 'info'}
                    />
                  </Tooltip>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && bun run build && cd ..`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/optimize/pages/CampaignListPage.tsx
git commit -m "feat(frontend): implement CampaignListPage with status cards"
```

---

### Task 9: Campaign Detail Page — Layout & Stats Header

**Files:**
- Modify: `frontend/src/features/optimize/pages/CampaignDetailPage.tsx` (replace placeholder)

- [ ] **Step 1: Implement layout with stats header and chart slots**

Replace `frontend/src/features/optimize/pages/CampaignDetailPage.tsx`:

```typescript
import { useParams } from 'react-router';
import { Box, Card, CardContent, Chip, Grid, LinearProgress, Typography } from '@mui/material';
import PageHeader from '@/components/PageHeader';
import StatsCard from '@/components/StatsCard';
import { useCampaignDetail, useCampaignProgress, useFeatureImportance } from '../hooks';
import ScoreProgressChart from '../components/ScoreProgressChart';
import ParameterHeatmap from '../components/ParameterHeatmap';
import ParameterSweepChart from '../components/ParameterSweepChart';
import PredictionSurface from '../components/PredictionSurface';
import FeatureImportance from '../components/FeatureImportance';
import UncertaintySurface from '../components/UncertaintySurface';
import RecommendationHistory from '../components/RecommendationHistory';

const phaseColor: Record<string, 'info' | 'warning' | 'success'> = {
  random: 'info',
  learning: 'warning',
  optimizing: 'success',
};

export default function CampaignDetailPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: campaign, isLoading: loadingDetail } = useCampaignDetail(campaignId!);
  const { data: progress, isLoading: loadingProgress } = useCampaignProgress(campaignId!);
  const { data: shap } = useFeatureImportance(campaignId!);

  if (loadingDetail || loadingProgress) return <LinearProgress />;
  if (!campaign || !progress) return null;

  // Determine default X/Y params from SHAP or fallback
  const continuousParams = (campaign.effective_ranges ?? [])
    .filter((r) => r.allowed_values == null)
    .map((r) => r.parameter_name);
  const defaultX = shap?.parameters?.[0] ?? continuousParams[0] ?? '';
  const defaultY = shap?.parameters?.[1] ?? continuousParams[1] ?? '';

  // Top N params for 1D sweeps
  const sweepParams = shap
    ? shap.parameters.slice(0, 4).filter((p) => continuousParams.includes(p))
    : continuousParams;

  const title = `${campaign.bean_name ?? 'Campaign'} — ${campaign.brew_setup_name ?? ''}`;

  return (
    <Box>
      <PageHeader
        title={title}
        breadcrumbs={[
          { label: 'Optimize', to: '/optimize' },
          { label: campaign.bean_name ?? campaignId! },
        ]}
      />

      {/* Stats header */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card sx={{ minWidth: 140 }}>
            <CardContent>
              <Typography variant="body2" color="text.secondary">Phase</Typography>
              <Chip
                label={progress.phase}
                color={phaseColor[progress.phase] ?? 'default'}
                sx={{ mt: 0.5 }}
              />
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <StatsCard
            label="Shots / Best"
            value={`${progress.measurement_count} / ${progress.best_score?.toFixed(1) ?? '—'}`}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <StatsCard
            label="Convergence"
            value={progress.convergence.status.replace(/_/g, ' ')}
          />
        </Grid>
      </Grid>

      {/* Chart 1: Score Progress */}
      <Section title="Score Progress">
        <ScoreProgressChart history={progress.score_history} />
      </Section>

      {/* Chart 2: Parameter Heatmap */}
      <Section title="Parameter Exploration">
        <ParameterHeatmap
          campaignId={campaignId!}
          params={continuousParams}
          defaultX={defaultX}
          defaultY={defaultY}
        />
      </Section>

      {/* Charts 3-4: 1D Sweeps */}
      {sweepParams.length > 0 && (
        <Section title="Parameter Sweeps">
          <Grid container spacing={2}>
            {sweepParams.map((param) => (
              <Grid size={{ xs: 12, md: 6 }} key={param}>
                <ParameterSweepChart campaignId={campaignId!} param={param} />
              </Grid>
            ))}
          </Grid>
        </Section>
      )}

      {/* Chart 5: 2D Prediction Surface */}
      <Section title="Prediction Surface">
        <PredictionSurface
          campaignId={campaignId!}
          params={continuousParams}
          defaultX={defaultX}
          defaultY={defaultY}
        />
      </Section>

      {/* Chart 6: Feature Importance */}
      <Section title="Feature Importance">
        <FeatureImportance campaignId={campaignId!} />
      </Section>

      {/* Chart 7: Uncertainty Surface */}
      <Section title="Uncertainty Map">
        <UncertaintySurface
          campaignId={campaignId!}
          params={continuousParams}
          defaultX={defaultX}
          defaultY={defaultY}
        />
      </Section>

      {/* Chart 8: Recommendation History */}
      <Section title="Recommendation History">
        <RecommendationHistory campaignId={campaignId!} />
      </Section>
    </Box>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      {children}
    </Box>
  );
}
```

> **Note:** This references chart components not yet created. The next tasks create them. Build will fail until all are implemented. If iterative builds are required, create stub exports for each chart first.

- [ ] **Step 2: Create stub chart components for build**

Create stubs for each chart component (each file exports a default component returning a placeholder `<Box>`). All in `frontend/src/features/optimize/components/`:

For each of `ScoreProgressChart.tsx`, `ParameterHeatmap.tsx`, `ParameterSweepChart.tsx`, `PredictionSurface.tsx`, `FeatureImportance.tsx`, `UncertaintySurface.tsx`, `RecommendationHistory.tsx`, `ParamSelector.tsx`:

```typescript
import { Box, Typography } from '@mui/material';
export default function ComponentName() {
  return <Box sx={{ p: 2 }}><Typography color="text.secondary">Coming soon</Typography></Box>;
}
```

(Use the correct prop signatures from the detail page — e.g., `ScoreProgressChart` receives `{ history }`, `ParameterHeatmap` receives `{ campaignId, params, defaultX, defaultY }`, etc.)

- [ ] **Step 3: Verify build**

Run: `cd frontend && bun run build && cd ..`

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/optimize/pages/CampaignDetailPage.tsx frontend/src/features/optimize/components/
git commit -m "feat(frontend): implement CampaignDetailPage layout with stats header and chart stubs"
```

---

### Task 10: ScoreProgressChart + ParamSelector

**Files:**
- Modify: `frontend/src/features/optimize/components/ScoreProgressChart.tsx`
- Modify: `frontend/src/features/optimize/components/ParamSelector.tsx`

- [ ] **Step 1: Implement ScoreProgressChart**

Replace `frontend/src/features/optimize/components/ScoreProgressChart.tsx`:

```typescript
import { useTheme } from '@mui/material';
import PlotlyChart from '@/components/PlotlyChart';
import type { ScoreHistoryEntry } from '../hooks';

interface Props {
  history: ScoreHistoryEntry[];
}

export default function ScoreProgressChart({ history }: Props) {
  const theme = useTheme();

  const normal = history.filter((e) => !e.is_failed && e.score != null);
  const failed = history.filter((e) => e.is_failed);

  // Cumulative best
  let best = -Infinity;
  const cumBest = normal.map((e) => {
    best = Math.max(best, e.score!);
    return { x: e.shot_number, y: best };
  });

  return (
    <PlotlyChart
      data={[
        {
          x: normal.map((e) => e.shot_number),
          y: normal.map((e) => e.score),
          mode: 'markers',
          type: 'scatter',
          name: 'Score',
          marker: { color: theme.palette.warning.main, size: 8 },
          hovertemplate: 'Shot %{x}<br>Score: %{y:.1f}<extra></extra>',
        },
        {
          x: failed.map((e) => e.shot_number),
          y: failed.map(() => 0),
          mode: 'markers',
          type: 'scatter',
          name: 'Failed',
          marker: { color: theme.palette.error.main, symbol: 'x', size: 10 },
          hovertemplate: 'Shot %{x}<br>Failed<extra></extra>',
        },
        {
          x: cumBest.map((p) => p.x),
          y: cumBest.map((p) => p.y),
          mode: 'lines',
          type: 'scatter',
          name: 'Best',
          line: { color: theme.palette.success.main, width: 2 },
          hovertemplate: 'Best: %{y:.1f}<extra></extra>',
        },
      ]}
      layout={{
        xaxis: { title: 'Shot #' },
        yaxis: { title: 'Score', range: [0, 10.5] },
        showlegend: true,
        legend: { orientation: 'h', y: -0.2 },
        height: 350,
      }}
    />
  );
}
```

- [ ] **Step 2: Implement ParamSelector**

Replace `frontend/src/features/optimize/components/ParamSelector.tsx`:

```typescript
import { Box, FormControl, InputLabel, MenuItem, Select } from '@mui/material';

interface Props {
  params: string[];
  xValue: string;
  yValue: string;
  onXChange: (v: string) => void;
  onYChange: (v: string) => void;
}

export default function ParamSelector({ params, xValue, yValue, onXChange, onYChange }: Props) {
  return (
    <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
      <FormControl size="small" sx={{ minWidth: 160 }}>
        <InputLabel>X Axis</InputLabel>
        <Select value={xValue} label="X Axis" onChange={(e) => onXChange(e.target.value)}>
          {params.map((p) => (
            <MenuItem key={p} value={p}>{p.replace(/_/g, ' ')}</MenuItem>
          ))}
        </Select>
      </FormControl>
      <FormControl size="small" sx={{ minWidth: 160 }}>
        <InputLabel>Y Axis</InputLabel>
        <Select value={yValue} label="Y Axis" onChange={(e) => onYChange(e.target.value)}>
          {params.map((p) => (
            <MenuItem key={p} value={p}>{p.replace(/_/g, ' ')}</MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  );
}
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && bun run build && cd ..`

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/optimize/components/ScoreProgressChart.tsx frontend/src/features/optimize/components/ParamSelector.tsx
git commit -m "feat(frontend): implement ScoreProgressChart and ParamSelector components"
```

---

### Task 11: ParameterHeatmap

**Files:**
- Modify: `frontend/src/features/optimize/components/ParameterHeatmap.tsx`

- [ ] **Step 1: Implement ParameterHeatmap**

Replace `frontend/src/features/optimize/components/ParameterHeatmap.tsx`:

```typescript
import { useState } from 'react';
import { Box, Typography, useTheme } from '@mui/material';
import PlotlyChart from '@/components/PlotlyChart';
import { usePosterior } from '../hooks';
import ParamSelector from './ParamSelector';

interface Props {
  campaignId: string;
  params: string[];
  defaultX: string;
  defaultY: string;
}

export default function ParameterHeatmap({ campaignId, params, defaultX, defaultY }: Props) {
  const theme = useTheme();
  const [xParam, setXParam] = useState(defaultX);
  const [yParam, setYParam] = useState(defaultY);

  // Use the posterior endpoint's measurements overlay for actual brew parameter values
  const { data, isError } = usePosterior(campaignId, `${xParam},${yParam}`, 5);

  if (params.length < 2) return null;

  const measurements = data?.measurements ?? [];

  if (isError || measurements.length === 0) {
    return (
      <>
        <ParamSelector params={params} xValue={xParam} yValue={yParam} onXChange={setXParam} onYChange={setYParam} />
        <Box sx={{ p: 2, textAlign: 'center' }}>
          <Typography color="text.secondary">Need more data for parameter heatmap</Typography>
        </Box>
      </>
    );
  }

  const xVals = measurements.map((m) => m.values[xParam]).filter((v) => v != null);
  const yVals = measurements.map((m) => m.values[yParam]).filter((v) => v != null);
  const scores = measurements
    .filter((m) => m.values[xParam] != null && m.values[yParam] != null)
    .map((m) => m.score);

  return (
    <>
      <ParamSelector
        params={params}
        xValue={xParam}
        yValue={yParam}
        onXChange={setXParam}
        onYChange={setYParam}
      />
      <PlotlyChart
        data={[
          {
            x: xVals,
            y: yVals,
            mode: 'markers',
            type: 'scatter',
            marker: {
              color: scores,
              colorscale: 'RdYlGn',
              cmin: 1,
              cmax: 10,
              size: 12,
              colorbar: { title: 'Score' },
            },
            hovertemplate: `${xParam}: %{x:.1f}<br>${yParam}: %{y:.1f}<br>Score: %{marker.color:.1f}<extra></extra>`,
          },
        ]}
        layout={{
          xaxis: { title: xParam.replace(/_/g, ' ') },
          yaxis: { title: yParam.replace(/_/g, ' ') },
          height: 400,
        }}
      />
    </>
  );
}

- [ ] **Step 2: Verify build, commit**

```bash
cd frontend && bun run build && cd ..
git add frontend/src/features/optimize/components/ParameterHeatmap.tsx
git commit -m "feat(frontend): implement ParameterHeatmap with colored scatter plot"
```

---

### Task 12: ParameterSweepChart (1D Posterior)

**Files:**
- Modify: `frontend/src/features/optimize/components/ParameterSweepChart.tsx`

- [ ] **Step 1: Implement ParameterSweepChart**

Replace `frontend/src/features/optimize/components/ParameterSweepChart.tsx`:

```typescript
import { Box, Typography } from '@mui/material';
import { useTheme } from '@mui/material';
import PlotlyChart from '@/components/PlotlyChart';
import { usePosterior } from '../hooks';

interface Props {
  campaignId: string;
  param: string;
}

export default function ParameterSweepChart({ campaignId, param }: Props) {
  const theme = useTheme();
  const { data, isLoading, isError } = usePosterior(campaignId, param, 50);

  if (isLoading) return <Typography color="text.secondary">Loading...</Typography>;
  if (isError || !data) {
    return (
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography color="text.secondary">Need more data for {param}</Typography>
      </Box>
    );
  }

  const xValues = data.grid[0];
  const mean = data.mean as number[];
  const std = data.std as number[];
  const upper = mean.map((m, i) => m + std[i]);
  const lower = mean.map((m, i) => m - std[i]);

  const measX = data.measurements
    .map((m) => m.values[param])
    .filter((v) => v != null);
  const measY = data.measurements
    .map((m) => m.score)
    .filter((_, i) => data.measurements[i].values[param] != null);

  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        {param.replace(/_/g, ' ')}
      </Typography>
      <PlotlyChart
        data={[
          // Upper bound (invisible line for fill)
          {
            x: xValues,
            y: upper,
            mode: 'lines',
            type: 'scatter',
            line: { width: 0 },
            showlegend: false,
            hoverinfo: 'skip' as const,
          },
          // Lower bound with fill to upper
          {
            x: xValues,
            y: lower,
            mode: 'lines',
            type: 'scatter',
            fill: 'tonexty',
            fillcolor: `${theme.palette.primary.main}22`,
            line: { width: 0 },
            showlegend: false,
            hoverinfo: 'skip' as const,
          },
          // Mean line
          {
            x: xValues,
            y: mean,
            mode: 'lines',
            type: 'scatter',
            name: 'Predicted',
            line: { color: theme.palette.primary.main, width: 2 },
            hovertemplate: '%{x:.1f}<br>Score: %{y:.2f}<extra></extra>',
          },
          // Actual measurements
          {
            x: measX,
            y: measY,
            mode: 'markers',
            type: 'scatter',
            name: 'Actual',
            marker: { color: theme.palette.warning.main, size: 8 },
            hovertemplate: '%{x:.1f}<br>Score: %{y:.1f}<extra></extra>',
          },
        ]}
        layout={{
          xaxis: { title: param.replace(/_/g, ' ') },
          yaxis: { title: 'Predicted Score' },
          height: 280,
          showlegend: false,
        }}
      />
    </Box>
  );
}
```

- [ ] **Step 2: Verify build, commit**

```bash
cd frontend && bun run build && cd ..
git add frontend/src/features/optimize/components/ParameterSweepChart.tsx
git commit -m "feat(frontend): implement 1D ParameterSweepChart with uncertainty band"
```

---

### Task 13: PredictionSurface + UncertaintySurface

**Files:**
- Modify: `frontend/src/features/optimize/components/PredictionSurface.tsx`
- Modify: `frontend/src/features/optimize/components/UncertaintySurface.tsx`

Both are 2D contour charts using the same `usePosterior` hook but mapping `mean` vs `std`.

- [ ] **Step 1: Implement PredictionSurface**

Replace `frontend/src/features/optimize/components/PredictionSurface.tsx`:

```typescript
import { useState } from 'react';
import { Box, Typography } from '@mui/material';
import PlotlyChart from '@/components/PlotlyChart';
import { usePosterior } from '../hooks';
import ParamSelector from './ParamSelector';

interface Props {
  campaignId: string;
  params: string[];
  defaultX: string;
  defaultY: string;
}

export default function PredictionSurface({ campaignId, params, defaultX, defaultY }: Props) {
  const [xParam, setXParam] = useState(defaultX);
  const [yParam, setYParam] = useState(defaultY);
  const { data, isError } = usePosterior(
    campaignId,
    `${xParam},${yParam}`,
    20,
  );

  if (params.length < 2) return null;

  if (isError || !data) {
    return (
      <>
        <ParamSelector params={params} xValue={xParam} yValue={yParam} onXChange={setXParam} onYChange={setYParam} />
        <Box sx={{ p: 2, textAlign: 'center' }}>
          <Typography color="text.secondary">Need more data for prediction surface</Typography>
        </Box>
      </>
    );
  }

  const measX = data.measurements.map((m) => m.values[xParam]);
  const measY = data.measurements.map((m) => m.values[yParam]);

  return (
    <>
      <ParamSelector params={params} xValue={xParam} yValue={yParam} onXChange={setXParam} onYChange={setYParam} />
      <PlotlyChart
        data={[
          {
            x: data.grid[0],
            y: data.grid[1],
            z: data.mean as number[][],
            type: 'contour',
            colorscale: 'RdYlGn',
            colorbar: { title: 'Score' },
            hovertemplate: `${xParam}: %{x:.1f}<br>${yParam}: %{y:.1f}<br>Score: %{z:.2f}<extra></extra>`,
          },
          {
            x: measX,
            y: measY,
            mode: 'markers',
            type: 'scatter',
            name: 'Measurements',
            marker: { color: 'white', size: 7, line: { color: 'black', width: 1 } },
            hovertemplate: `${xParam}: %{x:.1f}<br>${yParam}: %{y:.1f}<extra></extra>`,
          },
        ]}
        layout={{
          xaxis: { title: xParam.replace(/_/g, ' ') },
          yaxis: { title: yParam.replace(/_/g, ' ') },
          height: 450,
        }}
      />
    </>
  );
}
```

- [ ] **Step 2: Implement UncertaintySurface**

Replace `frontend/src/features/optimize/components/UncertaintySurface.tsx`. Same structure as PredictionSurface but maps `std` instead of `mean`:

```typescript
import { useState } from 'react';
import { Box, Typography } from '@mui/material';
import PlotlyChart from '@/components/PlotlyChart';
import { usePosterior } from '../hooks';
import ParamSelector from './ParamSelector';

interface Props {
  campaignId: string;
  params: string[];
  defaultX: string;
  defaultY: string;
}

export default function UncertaintySurface({ campaignId, params, defaultX, defaultY }: Props) {
  const [xParam, setXParam] = useState(defaultX);
  const [yParam, setYParam] = useState(defaultY);
  const { data, isError } = usePosterior(
    campaignId,
    `${xParam},${yParam}`,
    20,
  );

  if (params.length < 2) return null;

  if (isError || !data) {
    return (
      <>
        <ParamSelector params={params} xValue={xParam} yValue={yParam} onXChange={setXParam} onYChange={setYParam} />
        <Box sx={{ p: 2, textAlign: 'center' }}>
          <Typography color="text.secondary">Need more data for uncertainty map</Typography>
        </Box>
      </>
    );
  }

  return (
    <>
      <ParamSelector params={params} xValue={xParam} yValue={yParam} onXChange={setXParam} onYChange={setYParam} />
      <PlotlyChart
        data={[
          {
            x: data.grid[0],
            y: data.grid[1],
            z: data.std as number[][],
            type: 'contour',
            colorscale: [
              [0, '#1a237e'],
              [0.5, '#42a5f5'],
              [1, '#ffee58'],
            ],
            colorbar: { title: 'Uncertainty' },
            hovertemplate: `${xParam}: %{x:.1f}<br>${yParam}: %{y:.1f}<br>Std: %{z:.3f}<extra></extra>`,
          },
        ]}
        layout={{
          xaxis: { title: xParam.replace(/_/g, ' ') },
          yaxis: { title: yParam.replace(/_/g, ' ') },
          height: 450,
        }}
      />
    </>
  );
}
```

- [ ] **Step 3: Verify build, commit**

```bash
cd frontend && bun run build && cd ..
git add frontend/src/features/optimize/components/PredictionSurface.tsx frontend/src/features/optimize/components/UncertaintySurface.tsx
git commit -m "feat(frontend): implement 2D PredictionSurface and UncertaintySurface contour charts"
```

---

### Task 14: FeatureImportance + RecommendationHistory

**Files:**
- Modify: `frontend/src/features/optimize/components/FeatureImportance.tsx`
- Modify: `frontend/src/features/optimize/components/RecommendationHistory.tsx`

- [ ] **Step 1: Implement FeatureImportance**

Replace `frontend/src/features/optimize/components/FeatureImportance.tsx`:

```typescript
import { Box, Typography } from '@mui/material';
import { useTheme } from '@mui/material';
import PlotlyChart from '@/components/PlotlyChart';
import { useFeatureImportance } from '../hooks';

interface Props {
  campaignId: string;
}

export default function FeatureImportance({ campaignId }: Props) {
  const theme = useTheme();
  const { data, isError } = useFeatureImportance(campaignId);

  if (isError || !data) {
    return (
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography color="text.secondary">
          Need at least 3 measurements for feature importance
        </Typography>
      </Box>
    );
  }

  // Reverse for horizontal bar (Plotly renders bottom-to-top)
  const names = [...data.parameters].reverse();
  const values = [...data.importance].reverse();

  return (
    <PlotlyChart
      data={[
        {
          x: values,
          y: names,
          type: 'bar',
          orientation: 'h',
          marker: { color: theme.palette.primary.main },
          hovertemplate: '%{y}: %{x:.4f}<extra></extra>',
        },
      ]}
      layout={{
        xaxis: { title: 'SHAP Importance' },
        height: Math.max(200, names.length * 40 + 80),
        margin: { l: 120 },
      }}
    />
  );
}
```

- [ ] **Step 2: Implement RecommendationHistory**

Replace `frontend/src/features/optimize/components/RecommendationHistory.tsx`:

```typescript
import { Box, Chip, Typography } from '@mui/material';
import type { GridColDef } from '@mui/x-data-grid';
import DataTable from '@/components/DataTable';
import { useCampaignRecommendations, type Recommendation } from '../hooks';
import { usePagination } from '@/utils/pagination';

const phaseColor: Record<string, 'info' | 'warning' | 'success'> = {
  random: 'info',
  learning: 'warning',
  optimizing: 'success',
};

interface Props {
  campaignId: string;
}

export default function RecommendationHistory({ campaignId }: Props) {
  const { data: recs, isLoading } = useCampaignRecommendations(campaignId);
  const { paginationModel, onPaginationModelChange, sortModel, onSortModelChange } =
    usePagination({ field: 'created_at', sort: 'desc' });

  if (!recs || recs.length === 0) {
    return (
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography color="text.secondary">No recommendations yet</Typography>
      </Box>
    );
  }

  // Build columns dynamically from first recommendation's parameter keys
  const paramKeys = Object.keys(recs[0]?.parameter_values ?? {}).slice(0, 4);

  const columns: GridColDef[] = [
    {
      field: 'index',
      headerName: '#',
      width: 60,
      renderCell: (params) => params.api.getAllRowIds().indexOf(params.id) + 1,
      sortable: false,
    },
    {
      field: 'phase',
      headerName: 'Phase',
      width: 110,
      renderCell: (params) => (
        <Chip label={params.value} size="small" color={phaseColor[params.value] ?? 'default'} />
      ),
    },
    ...paramKeys.map((key) => ({
      field: `param_${key}`,
      headerName: key.replace(/_/g, ' '),
      width: 120,
      valueGetter: (_: unknown, row: Recommendation) =>
        row.parameter_values[key] != null
          ? Number(row.parameter_values[key]).toFixed(1)
          : '—',
    })),
    {
      field: 'predicted_score',
      headerName: 'Predicted',
      width: 130,
      renderCell: (params) => {
        const row = params.row as Recommendation;
        if (row.predicted_score == null) return '—';
        const std = row.predicted_std != null ? ` \u00b1${row.predicted_std.toFixed(1)}` : '';
        return `${row.predicted_score.toFixed(1)}${std}`;
      },
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 100,
      renderCell: (params) => {
        const color = params.value === 'brewed' ? 'success' : params.value === 'skipped' ? 'default' : 'warning';
        return <Chip label={params.value} size="small" color={color as 'success' | 'default' | 'warning'} />;
      },
    },
    {
      field: 'brew_score',
      headerName: 'Brew Score',
      width: 100,
      valueGetter: (_: unknown, row: Recommendation) =>
        row.brew_id ? '—' : '', // Placeholder: actual brew score requires a join/lookup
      // NOTE for executor: To show the linked brew's taste score, either
      // extend the RecommendationRead backend schema to include brew_score,
      // or do a client-side lookup. The simplest approach is adding an
      // optional brew_score field to the backend RecommendationRead schema.
    },
    {
      field: 'created_at',
      headerName: 'Created',
      width: 160,
      valueFormatter: (value: string) => new Date(value).toLocaleDateString(),
    },
  ];

  return (
    <DataTable
      columns={columns}
      rows={recs}
      total={recs.length}
      loading={isLoading}
      paginationModel={paginationModel}
      onPaginationModelChange={onPaginationModelChange}
      sortModel={sortModel}
      onSortModelChange={onSortModelChange}
    />
  );
}
```

- [ ] **Step 3: Verify build, commit**

```bash
cd frontend && bun run build && cd ..
git add frontend/src/features/optimize/components/FeatureImportance.tsx frontend/src/features/optimize/components/RecommendationHistory.tsx
git commit -m "feat(frontend): implement FeatureImportance bar chart and RecommendationHistory table"
```

---

## Phase D: BrewWizard Suggest Integration

### Task 15: SuggestButton + BrewWizard + BrewStepParams Integration

**Files:**
- Create: `frontend/src/features/optimize/components/SuggestButton.tsx`
- Modify: `frontend/src/features/brews/components/BrewWizard.tsx`
- Modify: `frontend/src/features/brews/components/BrewStepParams.tsx`

- [ ] **Step 1: Create SuggestButton component**

Create `frontend/src/features/optimize/components/SuggestButton.tsx`:

```typescript
import { Button, CircularProgress } from '@mui/material';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import { useSuggest, type Recommendation } from '../hooks';
import { useNotification } from '@/components/NotificationProvider';

interface Props {
  beanId: string;
  brewSetupId: string;
  onSuggestion: (rec: Recommendation, campaignId: string) => void;
  disabled?: boolean;
}

export default function SuggestButton({ beanId, brewSetupId, onSuggestion, disabled }: Props) {
  const suggest = useSuggest();
  const { notify } = useNotification();

  const handleClick = async () => {
    try {
      const { recommendation, campaignId } = await suggest.mutateAsync({
        beanId,
        brewSetupId,
      });
      onSuggestion(recommendation, campaignId);
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Suggestion failed', 'error');
    }
  };

  return (
    <Button
      variant="outlined"
      startIcon={suggest.isPending ? <CircularProgress size={18} /> : <AutoFixHighIcon />}
      onClick={handleClick}
      disabled={disabled || suggest.isPending || !beanId || !brewSetupId}
    >
      {suggest.isPending ? 'Computing...' : 'Get Suggestion'}
    </Button>
  );
}
```

- [ ] **Step 2: Add suggestion state to BrewWizard**

Modify `frontend/src/features/brews/components/BrewWizard.tsx`:

Add imports at top:
```typescript
import SuggestButton from '@/features/optimize/components/SuggestButton';
import { useLinkRecommendation, type Recommendation } from '@/features/optimize/hooks';
```

Add suggestion state after existing state declarations (~line 90):
```typescript
const [suggestion, setSuggestion] = useState<{
  recommendation: Recommendation;
  campaignId: string;
} | null>(null);

const linkRec = useLinkRecommendation();
```

Add suggestion handler:
```typescript
const handleSuggestion = (rec: Recommendation, campaignId: string) => {
  setSuggestion({ recommendation: rec, campaignId });
  // Auto-fill parameter fields from recommendation values
  const vals = rec.parameter_values;
  const patch: Partial<ParamsData> = {};
  if (vals.temperature != null) patch.temperature = String(vals.temperature);
  if (vals.dose != null) patch.dose = String(vals.dose);
  if (vals.yield_amount != null) patch.yield_amount = String(vals.yield_amount);
  if (vals.pressure != null) patch.pressure = String(vals.pressure);
  if (vals.flow_rate != null) patch.flow_rate = String(vals.flow_rate);
  if (vals.pre_infusion_time != null) patch.pre_infusion_time = String(vals.pre_infusion_time);
  if (vals.grind_setting_display != null) patch.grind_setting_display = String(vals.grind_setting_display);
  if (vals.total_time != null) patch.total_time = String(vals.total_time);
  // Note: bloom_weight, saturation, and other non-ParamsData fields from
  // the recommendation are intentionally skipped — they don't have
  // corresponding form fields in BrewStepParams.
  patchParams(patch);
};
```

Modify `handleSubmit` to link recommendation after save (~line 175):
```typescript
const handleSubmit = async (includeTaste: boolean) => {
  const body = buildBody(includeTaste);
  const newBrew = await createBrew.mutateAsync(body);

  // Link recommendation if suggestion was used
  if (suggestion) {
    try {
      await linkRec.mutateAsync({
        recommendationId: suggestion.recommendation.id,
        brewId: newBrew.id,
      });
    } catch {
      // Non-critical — don't block navigation
    }
  }

  notify('Brew logged successfully!');
  navigate(`/brews/${newBrew.id}`);
};
```

Pass suggestion to BrewStepParams (~line 201):
```typescript
{activeStep === 1 && (
  <BrewStepParams
    data={state.params}
    onChange={patchParams}
    rings={rings}
    suggestion={suggestion?.recommendation ?? null}
    suggestButton={
      state.setup.bag && state.setup.brew_setup ? (
        <SuggestButton
          beanId={state.setup.bag.bean_id}
          brewSetupId={state.setup.brew_setup.id}
          onSuggestion={handleSuggestion}
        />
      ) : undefined
    }
  />
)}
```

- [ ] **Step 3: Add suggestion display to BrewStepParams**

Modify `frontend/src/features/brews/components/BrewStepParams.tsx`:

Add to imports at the top of the file:
```typescript
import { Alert } from '@mui/material';
import type { Recommendation } from '@/features/optimize/hooks';
```

Update the props interface:
```typescript
interface BrewStepParamsProps {
  data: ParamsData;
  onChange: (patch: Partial<ParamsData>) => void;
  rings?: RingConfig[];
  suggestion?: Recommendation | null;
  suggestButton?: React.ReactNode;
}
```

Add the suggest button and info banner at the top of the form's return JSX (before the first TextField):

```tsx
{suggestButton && (
  <Box sx={{ mb: 2 }}>
    {suggestButton}
  </Box>
)}

{suggestion && suggestion.predicted_score != null && (
  <Alert severity="info" sx={{ mb: 2 }}>
    Suggested by optimizer (shot #{suggestion.parameter_values ? 'N' : '?'}, {suggestion.phase} phase)
    {suggestion.predicted_score != null && (
      <> — Predicted: ~{suggestion.predicted_score.toFixed(1)}
        {suggestion.predicted_std != null && (
          <> ({(suggestion.predicted_score - suggestion.predicted_std).toFixed(1)}–{(suggestion.predicted_score + suggestion.predicted_std).toFixed(1)})</>
        )}
      </>
    )}
  </Alert>
)}
```

Add `Alert` to the MUI imports. Add light blue border highlight to suggested fields via `sx` prop:

```typescript
const suggestedSx = suggestion ? { '& .MuiOutlinedInput-root': { borderColor: 'info.main' } } : {};
```

Apply `suggestedSx` to parameter TextFields that received suggestion values.

- [ ] **Step 4: Verify build**

Run: `cd frontend && bun run build && cd ..`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/optimize/components/SuggestButton.tsx frontend/src/features/brews/components/BrewWizard.tsx frontend/src/features/brews/components/BrewStepParams.tsx
git commit -m "feat(frontend): add Suggest button to BrewWizard with auto-fill and recommendation linking"
```

---

## Phase E: Person Preferences & Existing Mods

### Task 16: Person Preference Chart Components

**Files:**
- Create: 5 chart components in `frontend/src/features/people/components/`

- [ ] **Step 1: Create TopBeansChart**

Create `frontend/src/features/people/components/TopBeansChart.tsx`:

```typescript
import { useTheme } from '@mui/material';
import PlotlyChart from '@/components/PlotlyChart';

interface Props {
  beans: { name: string; avg_score: number; brew_count: number }[];
}

export default function TopBeansChart({ beans }: Props) {
  const theme = useTheme();
  const sorted = [...beans].sort((a, b) => b.avg_score - a.avg_score);

  return (
    <PlotlyChart
      data={[
        {
          x: sorted.map((b) => b.avg_score),
          y: sorted.map((b) => b.name),
          type: 'bar',
          orientation: 'h',
          marker: { color: theme.palette.primary.main },
          text: sorted.map((b) => `${b.brew_count} brews`),
          textposition: 'auto',
          hovertemplate: '%{y}<br>Avg: %{x:.1f}<br>%{text}<extra></extra>',
        },
      ]}
      layout={{
        xaxis: { title: 'Avg Score', range: [0, 10] },
        height: Math.max(200, sorted.length * 35 + 80),
        margin: { l: 140 },
      }}
    />
  );
}
```

- [ ] **Step 2: Create FlavorRadar**

Create `frontend/src/features/people/components/FlavorRadar.tsx`:

```typescript
import { useTheme } from '@mui/material';
import PlotlyChart from '@/components/PlotlyChart';

interface Props {
  profile: { tag: string; frequency: number }[];
}

export default function FlavorRadar({ profile }: Props) {
  const theme = useTheme();
  if (profile.length === 0) return null;

  const tags = profile.map((p) => p.tag);
  const values = profile.map((p) => p.frequency);

  return (
    <PlotlyChart
      data={[
        {
          type: 'scatterpolar',
          r: [...values, values[0]], // close the polygon
          theta: [...tags, tags[0]],
          fill: 'toself',
          fillcolor: `${theme.palette.primary.main}33`,
          line: { color: theme.palette.primary.main },
          name: 'Flavors',
        },
      ]}
      layout={{
        polar: {
          radialaxis: { visible: true, color: theme.palette.text.secondary },
          angularaxis: { color: theme.palette.text.secondary },
          bgcolor: 'transparent',
        },
        height: 350,
        showlegend: false,
      }}
    />
  );
}
```

- [ ] **Step 3: Create RoastDonut**

Create `frontend/src/features/people/components/RoastDonut.tsx`:

```typescript
import PlotlyChart from '@/components/PlotlyChart';

interface Props {
  roast: Record<string, number>;
}

export default function RoastDonut({ roast }: Props) {
  const labels = Object.keys(roast);
  const values = Object.values(roast);
  if (labels.length === 0) return null;

  return (
    <PlotlyChart
      data={[
        {
          labels,
          values,
          type: 'pie',
          hole: 0.5,
          marker: { colors: ['#f9e79f', '#d4a574', '#6d4c41'] }, // light, medium, dark
          textinfo: 'label+percent',
          hovertemplate: '%{label}: %{value} brews (%{percent})<extra></extra>',
        },
      ]}
      layout={{ height: 300, showlegend: true, legend: { orientation: 'h', y: -0.1 } }}
    />
  );
}
```

- [ ] **Step 4: Create OriginPreferences**

Create `frontend/src/features/people/components/OriginPreferences.tsx`:

```typescript
import { useTheme } from '@mui/material';
import PlotlyChart from '@/components/PlotlyChart';

interface Props {
  origins: { origin: string; avg_score: number; brew_count: number }[];
}

export default function OriginPreferences({ origins }: Props) {
  const theme = useTheme();
  const sorted = [...origins].sort((a, b) => b.avg_score - a.avg_score);

  return (
    <PlotlyChart
      data={[
        {
          x: sorted.map((o) => o.avg_score),
          y: sorted.map((o) => o.origin),
          type: 'bar',
          orientation: 'h',
          marker: { color: theme.palette.secondary.main },
          hovertemplate: '%{y}<br>Avg: %{x:.1f}<extra></extra>',
        },
      ]}
      layout={{
        xaxis: { title: 'Avg Score', range: [0, 10] },
        height: Math.max(200, sorted.length * 35 + 80),
        margin: { l: 120 },
      }}
    />
  );
}
```

- [ ] **Step 5: Create MethodBreakdown**

Create `frontend/src/features/people/components/MethodBreakdown.tsx`:

```typescript
import { useTheme } from '@mui/material';
import PlotlyChart from '@/components/PlotlyChart';

interface Props {
  methods: { method: string; brew_count: number; avg_score: number }[];
}

export default function MethodBreakdown({ methods }: Props) {
  const theme = useTheme();

  return (
    <PlotlyChart
      data={[
        {
          x: methods.map((m) => m.method),
          y: methods.map((m) => m.brew_count),
          type: 'bar',
          name: 'Brews',
          marker: { color: theme.palette.primary.main },
          hovertemplate: '%{x}<br>Brews: %{y}<extra></extra>',
        },
        {
          x: methods.map((m) => m.method),
          y: methods.map((m) => m.avg_score),
          type: 'bar',
          name: 'Avg Score',
          marker: { color: theme.palette.secondary.main },
          yaxis: 'y2',
          hovertemplate: '%{x}<br>Avg: %{y:.1f}<extra></extra>',
        },
      ]}
      layout={{
        barmode: 'group',
        yaxis: { title: 'Brew Count' },
        yaxis2: { title: 'Avg Score', overlaying: 'y', side: 'right', range: [0, 10] },
        height: 350,
        legend: { orientation: 'h', y: -0.2 },
      }}
    />
  );
}
```

- [ ] **Step 6: Verify build, commit**

```bash
cd frontend && bun run build && cd ..
git add frontend/src/features/people/components/
git commit -m "feat(frontend): add person preference chart components (5 Plotly charts)"
```

---

### Task 17: PersonPreferencesPage + PeoplePage Navigation

**Files:**
- Modify: `frontend/src/features/people/pages/PersonPreferencesPage.tsx` (replace placeholder)
- Modify: `frontend/src/features/people/PeoplePage.tsx`

- [ ] **Step 1: Implement PersonPreferencesPage**

Replace `frontend/src/features/people/pages/PersonPreferencesPage.tsx`:

```typescript
import { useState } from 'react';
import { useParams } from 'react-router';
import { Box, Button, Grid, LinearProgress, Typography } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import PageHeader from '@/components/PageHeader';
import StatsCard from '@/components/StatsCard';
import PersonFormDialog from '../PersonFormDialog';
import { usePersonPreferences } from '@/features/optimize/hooks';
import TopBeansChart from '../components/TopBeansChart';
import FlavorRadar from '../components/FlavorRadar';
import RoastDonut from '../components/RoastDonut';
import OriginPreferences from '../components/OriginPreferences';
import MethodBreakdown from '../components/MethodBreakdown';

export default function PersonPreferencesPage() {
  const { personId } = useParams<{ personId: string }>();
  const { data, isLoading } = usePersonPreferences(personId!);
  const [editOpen, setEditOpen] = useState(false);

  if (isLoading) return <LinearProgress />;
  if (!data) return null;

  const { person, brew_stats, top_beans, flavor_profile, roast_preference, origin_preferences, method_breakdown } = data;

  return (
    <Box>
      <PageHeader
        title={`${person.name}'s Preferences`}
        breadcrumbs={[
          { label: 'People', to: '/people' },
          { label: person.name },
        ]}
        actions={
          <Button variant="outlined" startIcon={<EditIcon />} onClick={() => setEditOpen(true)}>
            Edit
          </Button>
        }
      />

      <PersonFormDialog
        open={editOpen}
        onClose={() => setEditOpen(false)}
        person={{ id: person.id, name: person.name }}
      />

      {/* Stats header */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 4 }}>
          <StatsCard label="Total Brews" value={brew_stats.total_brews} />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <StatsCard
            label="Average Score"
            value={brew_stats.avg_score?.toFixed(1) ?? '—'}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <StatsCard
            label="Favorite Method"
            value={brew_stats.favorite_method ?? '—'}
          />
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        {top_beans.length > 0 && (
          <Grid size={{ xs: 12, md: 6 }}>
            <Section title="Top Beans">
              <TopBeansChart beans={top_beans} />
            </Section>
          </Grid>
        )}

        {flavor_profile.length > 0 && (
          <Grid size={{ xs: 12, md: 6 }}>
            <Section title="Flavor Profile">
              <FlavorRadar profile={flavor_profile} />
            </Section>
          </Grid>
        )}

        {Object.keys(roast_preference).length > 0 && (
          <Grid size={{ xs: 12, md: 6 }}>
            <Section title="Roast Preference">
              <RoastDonut roast={roast_preference} />
            </Section>
          </Grid>
        )}

        {origin_preferences.length > 0 && (
          <Grid size={{ xs: 12, md: 6 }}>
            <Section title="Origin Preferences">
              <OriginPreferences origins={origin_preferences} />
            </Section>
          </Grid>
        )}

        {method_breakdown.length > 0 && (
          <Grid size={12}>
            <Section title="Method Breakdown">
              <MethodBreakdown methods={method_breakdown} />
            </Section>
          </Grid>
        )}
      </Grid>
    </Box>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      {children}
    </Box>
  );
}
```

- [ ] **Step 2: Update PeoplePage row click to navigate to preferences**

In `frontend/src/features/people/PeoplePage.tsx`, change the `onRowClick` handler (~line 62):

**Before:**
```typescript
onRowClick={(row) => { setEditPerson(row); setFormOpen(true); }}
```

**After:**
```typescript
onRowClick={(row) => navigate(`/people/${row.id}/preferences`)}
```

Add `useNavigate` import at top:
```typescript
import { useNavigate } from 'react-router';
```

Add inside the component:
```typescript
const navigate = useNavigate();
```

- [ ] **Step 3: Verify build, commit**

```bash
cd frontend && bun run build && cd ..
git add frontend/src/features/people/pages/PersonPreferencesPage.tsx frontend/src/features/people/PeoplePage.tsx
git commit -m "feat(frontend): implement PersonPreferencesPage and update PeoplePage row navigation"
```

---

### Task 18: TasteRadar Plotly Migration + Remove Recharts

**Files:**
- Modify: `frontend/src/components/TasteRadar.tsx`
- Modify: `frontend/package.json` (remove recharts)

- [ ] **Step 1: Remove Recharts**

```bash
cd frontend && bun remove recharts && cd ..
```

- [ ] **Step 2: Rewrite TasteRadar with Plotly**

Replace the entire contents of `frontend/src/components/TasteRadar.tsx`:

```typescript
import { useTheme } from '@mui/material';
import PlotlyChart from './PlotlyChart';

export interface TasteDataPoint {
  axis: string;
  value: number;
}

interface TasteRadarProps {
  data: TasteDataPoint[];
  maxValue?: number;
  size?: number;
}

export default function TasteRadar({ data, maxValue = 10, size = 300 }: TasteRadarProps) {
  const theme = useTheme();

  if (data.length === 0) return null;

  const axes = data.map((d) => d.axis);
  const values = data.map((d) => d.value);

  return (
    <PlotlyChart
      data={[
        {
          type: 'scatterpolar',
          r: [...values, values[0]], // close the polygon
          theta: [...axes, axes[0]],
          fill: 'toself',
          fillcolor: `${theme.palette.primary.main}4D`, // ~0.3 opacity
          line: { color: theme.palette.primary.main },
          name: 'Taste',
        },
      ]}
      layout={{
        polar: {
          radialaxis: {
            visible: true,
            range: [0, maxValue],
            color: theme.palette.text.secondary,
          },
          angularaxis: {
            color: theme.palette.text.secondary,
          },
          bgcolor: 'transparent',
        },
        height: size,
        showlegend: false,
        margin: { t: 30, r: 30, b: 30, l: 30 },
      }}
    />
  );
}

// Re-export the same helper functions for backwards compatibility.
// These map domain objects to TasteDataPoint arrays.

interface BrewTaste {
  acidity?: number | null;
  sweetness?: number | null;
  body?: number | null;
  bitterness?: number | null;
  balance?: number | null;
  aftertaste?: number | null;
}

export function brewTasteToRadar(taste: BrewTaste): TasteDataPoint[] {
  return [
    { axis: 'Acidity', value: taste.acidity ?? 0 },
    { axis: 'Sweetness', value: taste.sweetness ?? 0 },
    { axis: 'Body', value: taste.body ?? 0 },
    { axis: 'Bitterness', value: taste.bitterness ?? 0 },
    { axis: 'Balance', value: taste.balance ?? 0 },
    { axis: 'Aftertaste', value: taste.aftertaste ?? 0 },
  ];
}

interface BeanTaste {
  acidity?: number | null;
  sweetness?: number | null;
  body?: number | null;
  complexity?: number | null;
  aroma?: number | null;
  clean_cup?: number | null;
}

export function beanTasteToRadar(taste: BeanTaste): TasteDataPoint[] {
  return [
    { axis: 'Acidity', value: taste.acidity ?? 0 },
    { axis: 'Sweetness', value: taste.sweetness ?? 0 },
    { axis: 'Body', value: taste.body ?? 0 },
    { axis: 'Complexity', value: taste.complexity ?? 0 },
    { axis: 'Aroma', value: taste.aroma ?? 0 },
    { axis: 'Clean Cup', value: taste.clean_cup ?? 0 },
  ];
}

interface CuppingScores {
  dry_fragrance?: number | null;
  wet_aroma?: number | null;
  brightness?: number | null;
  flavor?: number | null;
  body?: number | null;
  finish?: number | null;
  sweetness?: number | null;
  clean_cup?: number | null;
  complexity?: number | null;
  uniformity?: number | null;
}

export function cuppingToRadar(scores: CuppingScores): TasteDataPoint[] {
  return [
    { axis: 'Dry Fragrance', value: scores.dry_fragrance ?? 0 },
    { axis: 'Wet Aroma', value: scores.wet_aroma ?? 0 },
    { axis: 'Brightness', value: scores.brightness ?? 0 },
    { axis: 'Flavor', value: scores.flavor ?? 0 },
    { axis: 'Body', value: scores.body ?? 0 },
    { axis: 'Finish', value: scores.finish ?? 0 },
    { axis: 'Sweetness', value: scores.sweetness ?? 0 },
    { axis: 'Clean Cup', value: scores.clean_cup ?? 0 },
    { axis: 'Complexity', value: scores.complexity ?? 0 },
    { axis: 'Uniformity', value: scores.uniformity ?? 0 },
  ];
}
```

- [ ] **Step 3: Verify all imports across codebase still work**

Run: `cd frontend && bun run build && cd ..`

Expected: Build succeeds. All existing pages that use TasteRadar (brew detail, cupping detail) continue to work.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/TasteRadar.tsx frontend/package.json frontend/bun.lock
git commit -m "refactor(frontend): migrate TasteRadar from Recharts to Plotly, remove recharts"
```

---

### Task 19: Dashboard Optimization Card

**Files:**
- Modify: `frontend/src/features/dashboard/DashboardPage.tsx`

- [ ] **Step 1: Add optimization summary to dashboard**

In `frontend/src/features/dashboard/DashboardPage.tsx`:

Add import:
```typescript
import { useCampaigns } from '@/features/optimize/hooks';
import { useNavigate } from 'react-router';
```

> **Note:** `useNavigate` may already be imported. Check first.

Add hook call inside the component:
```typescript
const { data: campaigns } = useCampaigns();
```

Compute summary:
```typescript
const activeCampaigns = campaigns?.length ?? 0;
const bestOverall = campaigns?.reduce(
  (best, c) => (c.best_score != null && (best == null || c.best_score > best) ? c.best_score : best),
  null as number | null,
);
```

Add a new section after the existing "Cuppings" section (before "Recent Brews"):

```tsx
{/* Optimization */}
<SectionLabel>Optimization</SectionLabel>
<StatRow>
  <Box onClick={() => navigate('/optimize')} sx={{ cursor: 'pointer' }}>
    <StatsCard
      label="Active Campaigns"
      value={activeCampaigns}
      icon={<OptimizeIcon />}
    />
  </Box>
  <StatsCard
    label="Best Score"
    value={bestOverall?.toFixed(1) ?? '—'}
  />
</StatRow>
```

Add import for the icon:
```typescript
import AutoFixHigh as OptimizeIcon from '@mui/icons-material/AutoFixHigh';
```

> **Note for executor:** `StatsCard` accepts `icon` but not `onClick`. The clickable card is wrapped in a `Box` with cursor styling. Verify that `SectionLabel` and `StatRow` are the helper components used in DashboardPage for section layout — match the existing pattern.

- [ ] **Step 2: Verify build, commit**

```bash
cd frontend && bun run build && cd ..
git add frontend/src/features/dashboard/DashboardPage.tsx
git commit -m "feat(frontend): add optimization summary card to dashboard"
```

---

## Final Verification

After all tasks are complete:

- [ ] **Backend:** `uv run pytest tests/integration/test_optimize_api.py -v --no-header` — all tests pass
- [ ] **Frontend:** `cd frontend && bun run build && cd ..` — clean build, no errors
- [ ] **Full test suite:** `uv run pytest --no-header` — no regressions
- [ ] **Manual check:** Start dev servers, navigate through all new pages, verify charts render
