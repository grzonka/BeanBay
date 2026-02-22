"""Integration tests for BayBE OptimizerService."""

import pandas as pd
import pytest

from app.services.optimizer import (
    DEFAULT_BOUNDS,
    BAYBE_PARAM_COLUMNS,
    OptimizerService,
    _bounds_fingerprint,
    _resolve_bounds,
)


pytestmark = pytest.mark.slow


async def test_create_campaign(optimizer_service, tmp_campaigns_dir):
    """get_or_create_campaign creates and persists a campaign."""
    campaign = optimizer_service.get_or_create_campaign("test-bean")
    assert campaign is not None

    campaign_file = tmp_campaigns_dir / "test-bean.json"
    assert campaign_file.exists()


async def test_recommend_returns_all_params(optimizer_service):
    """recommend() returns all 6 params + recommendation_id within bounds."""
    rec = await optimizer_service.recommend("test-bean")

    assert isinstance(rec, dict)
    for param in BAYBE_PARAM_COLUMNS:
        assert param in rec, f"Missing param: {param}"

    assert "recommendation_id" in rec
    assert rec["recommendation_id"]  # non-empty

    # Check bounds
    assert 15.0 <= rec["grind_setting"] <= 25.0
    assert 86.0 <= rec["temperature"] <= 96.0
    assert 55.0 <= rec["preinfusion_pct"] <= 100.0
    assert 18.5 <= rec["dose_in"] <= 20.0
    assert 36.0 <= rec["target_yield"] <= 50.0
    assert rec["saturation"] in ("yes", "no")


async def test_recommend_rounding(optimizer_service):
    """Recommendations are rounded to practical precision."""
    rec = await optimizer_service.recommend("rounding-bean")

    assert rec["grind_setting"] % 0.5 == 0, f"grind not rounded: {rec['grind_setting']}"
    assert rec["temperature"] % 1.0 == 0, f"temp not rounded: {rec['temperature']}"
    assert rec["preinfusion_pct"] % 5.0 == 0, f"preinfusion not rounded: {rec['preinfusion_pct']}"
    assert rec["dose_in"] % 0.5 == 0, f"dose not rounded: {rec['dose_in']}"
    assert rec["target_yield"] % 1.0 == 0, f"yield not rounded: {rec['target_yield']}"


async def test_add_measurement_and_recommend_again(optimizer_service, tmp_campaigns_dir):
    """Full cycle: recommend -> add measurement -> recommend again."""
    rec1 = await optimizer_service.recommend("cycle-bean")

    # Add measurement with recommended params
    params = {k: rec1[k] for k in BAYBE_PARAM_COLUMNS}
    optimizer_service.add_measurement("cycle-bean", {**params, "taste": 7.5})

    # Second recommendation should work
    rec2 = await optimizer_service.recommend("cycle-bean")
    assert all(p in rec2 for p in BAYBE_PARAM_COLUMNS)

    # Campaign file was updated
    campaign_file = tmp_campaigns_dir / "cycle-bean.json"
    assert campaign_file.exists()


async def test_campaign_persistence_across_restart(optimizer_service, tmp_campaigns_dir):
    """Campaign state survives service restart (new instance, same dir)."""
    # Create campaign and add measurement
    rec = await optimizer_service.recommend("persist-bean")
    params = {k: rec[k] for k in BAYBE_PARAM_COLUMNS}
    optimizer_service.add_measurement("persist-bean", {**params, "taste": 8.0})

    # Create new service instance (simulates restart)
    new_service = OptimizerService(tmp_campaigns_dir)
    campaign = new_service.get_or_create_campaign("persist-bean")

    # Campaign should have the measurement
    assert len(campaign.measurements) > 0

    # Should be able to recommend
    rec2 = await new_service.recommend("persist-bean")
    assert all(p in rec2 for p in BAYBE_PARAM_COLUMNS)


async def test_campaign_file_size_hybrid(optimizer_service, tmp_campaigns_dir):
    """Hybrid campaign JSON is <500KB (vs 20MB with discrete)."""
    rec = await optimizer_service.recommend("size-bean")
    params = {k: rec[k] for k in BAYBE_PARAM_COLUMNS}
    optimizer_service.add_measurement("size-bean", {**params, "taste": 7.0})

    campaign_file = tmp_campaigns_dir / "size-bean.json"
    file_size = campaign_file.stat().st_size
    assert file_size < 500_000, f"Campaign file too large: {file_size} bytes"


async def test_rebuild_campaign(optimizer_service, tmp_campaigns_dir):
    """rebuild_campaign creates a fresh campaign from measurement data."""
    # Add some measurements manually
    measurements = [
        {
            "grind_setting": 20.0,
            "temperature": 93.0,
            "preinfusion_pct": 75.0,
            "dose_in": 19.0,
            "target_yield": 40.0,
            "saturation": "yes",
            "taste": 7.0,
        },
        {
            "grind_setting": 21.0,
            "temperature": 94.0,
            "preinfusion_pct": 80.0,
            "dose_in": 19.5,
            "target_yield": 42.0,
            "saturation": "no",
            "taste": 8.5,
        },
    ]
    df = pd.DataFrame(measurements)

    campaign = optimizer_service.rebuild_campaign("rebuild-bean", df)
    assert campaign is not None
    assert len(campaign.measurements) == 2

    # Should be able to recommend from rebuilt campaign
    rec = await optimizer_service.recommend("rebuild-bean")
    assert all(p in rec for p in BAYBE_PARAM_COLUMNS)


# --- Parameter override tests ---


def test_resolve_bounds_defaults():
    """_resolve_bounds with no overrides returns DEFAULT_BOUNDS."""
    assert _resolve_bounds(None) == DEFAULT_BOUNDS
    assert _resolve_bounds({}) == DEFAULT_BOUNDS


def test_resolve_bounds_partial_override():
    """_resolve_bounds merges partial overrides onto defaults."""
    overrides = {"grind_setting": {"min": 18.0, "max": 22.0}}
    bounds = _resolve_bounds(overrides)
    assert bounds["grind_setting"] == (18.0, 22.0)
    # Other params unchanged
    assert bounds["temperature"] == DEFAULT_BOUNDS["temperature"]
    assert bounds["dose_in"] == DEFAULT_BOUNDS["dose_in"]


def test_resolve_bounds_partial_min_only():
    """_resolve_bounds can override just min, keeping default max."""
    overrides = {"temperature": {"min": 90.0}}
    bounds = _resolve_bounds(overrides)
    assert bounds["temperature"] == (90.0, 96.0)  # max stays default


def test_resolve_bounds_ignores_unknown_params():
    """_resolve_bounds ignores parameters not in DEFAULT_BOUNDS."""
    overrides = {"unknown_param": {"min": 1.0, "max": 10.0}}
    bounds = _resolve_bounds(overrides)
    assert bounds == DEFAULT_BOUNDS


def test_bounds_fingerprint_stable():
    """Same bounds produce the same fingerprint."""
    b1 = _resolve_bounds(None)
    b2 = _resolve_bounds({})
    assert _bounds_fingerprint(b1) == _bounds_fingerprint(b2)


def test_bounds_fingerprint_changes_with_overrides():
    """Different overrides produce different fingerprints."""
    fp_default = _bounds_fingerprint(_resolve_bounds(None))
    fp_custom = _bounds_fingerprint(_resolve_bounds({"grind_setting": {"min": 18.0, "max": 22.0}}))
    assert fp_default != fp_custom


async def test_recommend_with_overrides(optimizer_service):
    """Recommendations with custom bounds respect the narrowed range."""
    overrides = {
        "grind_setting": {"min": 20.0, "max": 22.0},
        "temperature": {"min": 92.0, "max": 94.0},
    }
    rec = await optimizer_service.recommend("override-bean", overrides)

    assert 20.0 <= rec["grind_setting"] <= 22.0
    assert 92.0 <= rec["temperature"] <= 94.0
    # Non-overridden params use defaults
    assert 55.0 <= rec["preinfusion_pct"] <= 100.0
    assert 18.5 <= rec["dose_in"] <= 20.0
    assert 36.0 <= rec["target_yield"] <= 50.0
    assert rec["saturation"] in ("yes", "no")


async def test_campaign_invalidation_on_override_change(optimizer_service, tmp_campaigns_dir):
    """Changing overrides rebuilds the campaign with new bounds."""
    # Create campaign with default bounds and add a measurement
    rec1 = await optimizer_service.recommend("invalidate-bean")
    params = {k: rec1[k] for k in BAYBE_PARAM_COLUMNS}
    optimizer_service.add_measurement("invalidate-bean", {**params, "taste": 7.0})

    campaign_before = optimizer_service.get_or_create_campaign("invalidate-bean")
    assert len(campaign_before.measurements) == 1

    # Now change overrides — campaign should rebuild with measurements preserved
    new_overrides = {"grind_setting": {"min": 20.0, "max": 22.0}}
    campaign_after = optimizer_service.get_or_create_campaign("invalidate-bean", new_overrides)

    # Measurements should be preserved after rebuild
    assert len(campaign_after.measurements) == 1

    # New recommendation should respect new bounds
    rec2 = await optimizer_service.recommend("invalidate-bean", new_overrides)
    assert 20.0 <= rec2["grind_setting"] <= 22.0


async def test_rebuild_campaign_with_overrides(optimizer_service):
    """rebuild_campaign respects custom overrides."""
    overrides = {"temperature": {"min": 90.0, "max": 92.0}}
    measurements = [
        {
            "grind_setting": 20.0,
            "temperature": 91.0,
            "preinfusion_pct": 75.0,
            "dose_in": 19.0,
            "target_yield": 40.0,
            "saturation": "yes",
            "taste": 7.0,
        },
    ]
    df = pd.DataFrame(measurements)
    campaign = optimizer_service.rebuild_campaign("rebuild-override-bean", df, overrides)
    assert len(campaign.measurements) == 1

    rec = await optimizer_service.recommend("rebuild-override-bean", overrides)
    assert 90.0 <= rec["temperature"] <= 92.0


# --- get_recommendation_insights tests ---


async def test_insights_random_phase(optimizer_service):
    """Fresh campaign (no measurements) returns phase='random' with no predictions."""
    rec = await optimizer_service.recommend("insights-random-bean")
    insights = optimizer_service.get_recommendation_insights("insights-random-bean", rec)

    assert insights["phase"] == "random"
    assert insights["phase_label"] == "Random exploration"
    assert "Exploring randomly" in insights["explanation"]
    assert insights["predicted_mean"] is None
    assert insights["predicted_std"] is None
    assert insights["predicted_range"] is None
    assert insights["shot_count"] == 0


async def test_insights_bayesian_phase(optimizer_service):
    """After 5+ measurements (switch_after=5), insights return phase='bayesian_early' with predictions."""
    # Get a recommendation first to establish the bean
    rec = await optimizer_service.recommend("insights-bayesian-bean")

    # Add 5 measurements so campaign switches to Bayesian phase
    params = {k: rec[k] for k in BAYBE_PARAM_COLUMNS}
    for taste in [6.0, 7.0, 7.5, 8.0, 8.5]:
        optimizer_service.add_measurement("insights-bayesian-bean", {**params, "taste": taste})

    rec2 = await optimizer_service.recommend("insights-bayesian-bean")
    insights = optimizer_service.get_recommendation_insights("insights-bayesian-bean", rec2)

    # With switch_after=5 and 5 measurements, we're in Bayesian mode
    # shot_count=5 < 8, so phase is bayesian_early
    assert insights["phase"] == "bayesian_early"
    assert insights["phase_label"] == "Learning"
    assert insights["shot_count"] == 5
    assert insights["predicted_mean"] is not None
    assert insights["predicted_std"] is not None
    assert insights["predicted_range"] is not None
    # Range string should contain the em dash separator
    assert "\u2013" in insights["predicted_range"]


async def test_insights_with_improvement(optimizer_service):
    """When latest shots show improvement and shot_count>=8, phase='bayesian' explanation mentions 'Zeroing in'."""
    bean_id = "insights-improve-bean"
    rec = await optimizer_service.recommend(bean_id)

    # Add 9 measurements — early ones low taste, last 3 higher (shows improvement)
    # 9 shots → shot_count=9 >= 8 → phase="bayesian"
    base_params = {k: rec[k] for k in BAYBE_PARAM_COLUMNS}
    for taste in [5.0, 6.0, 5.5, 6.0, 5.5, 6.0, 7.0, 8.0, 8.5]:
        optimizer_service.add_measurement(bean_id, {**base_params, "taste": taste})

    rec2 = await optimizer_service.recommend(bean_id)
    insights = optimizer_service.get_recommendation_insights(bean_id, rec2)

    assert insights["phase"] == "bayesian"
    assert insights["shot_count"] == 9
    # Last 3 best (8.0, 8.5) improved over previous best (max of first 6: 6.0)
    assert "Zeroing in" in insights["explanation"] or "improving" in insights["explanation"]


async def test_recommend_no_crash_on_second_call(optimizer_service):
    """recommend() twice for the same bean (with measurement in between) must not crash."""
    bean_id = "no-crash-bean"

    # First call
    rec1 = await optimizer_service.recommend(bean_id)
    assert isinstance(rec1, dict)
    for param in BAYBE_PARAM_COLUMNS:
        assert param in rec1

    # Add a measurement between calls
    params = {k: rec1[k] for k in BAYBE_PARAM_COLUMNS}
    optimizer_service.add_measurement(bean_id, {**params, "taste": 7.0})

    # Second call must NOT raise NotImplementedError (BayBE cache guard bug)
    rec2 = await optimizer_service.recommend(bean_id)
    assert isinstance(rec2, dict)
    for param in BAYBE_PARAM_COLUMNS:
        assert param in rec2
    assert "recommendation_id" in rec2


async def test_insights_bayesian_early_phase(optimizer_service):
    """With exactly 6 measurements (switch_after=5, so Bayesian), phase='bayesian_early', label='Learning'."""
    bean_id = "bayesian-early-bean"
    rec = await optimizer_service.recommend(bean_id)

    # Add 6 measurements → shot_count=6, which is >= 5 (Bayesian mode) but < 8 (bayesian_early)
    base_params = {k: rec[k] for k in BAYBE_PARAM_COLUMNS}
    for taste in [6.0, 6.5, 7.0, 7.0, 7.5, 7.5]:
        optimizer_service.add_measurement(bean_id, {**base_params, "taste": taste})

    rec2 = await optimizer_service.recommend(bean_id)
    insights = optimizer_service.get_recommendation_insights(bean_id, rec2)

    assert insights["phase"] == "bayesian_early"
    assert insights["phase_label"] == "Learning"
    assert "learning" in insights["explanation"].lower()
    assert insights["shot_count"] == 6
