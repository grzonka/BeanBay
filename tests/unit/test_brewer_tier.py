"""Unit tests for brewer tier derivation."""

from __future__ import annotations

from types import SimpleNamespace

from beanbay.utils.brewer_capabilities import TIER_LABELS, derive_tier


def _make_brewer(**overrides: str) -> SimpleNamespace:
    """Create a brewer-like object with sensible defaults.

    Parameters
    ----------
    **overrides : str
        Keyword arguments to override the default capability values.

    Returns
    -------
    SimpleNamespace
        Object with ``flow_control_type``, ``pressure_control_type``,
        ``preinfusion_type``, and ``temp_control_type`` attributes.
    """
    defaults = {
        "flow_control_type": "none",
        "pressure_control_type": "fixed",
        "preinfusion_type": "none",
        "temp_control_type": "none",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestDeriveTier:
    """Tests for derive_tier across all five tiers."""

    def test_tier_1_basic(self):
        brewer = _make_brewer()
        assert derive_tier(brewer) == 1

    def test_tier_1_preset_temp(self):
        # Preset temp is NOT pid/profiling, stays tier 1
        brewer = _make_brewer(temp_control_type="preset")
        assert derive_tier(brewer) == 1

    def test_tier_2_pid(self):
        brewer = _make_brewer(temp_control_type="pid")
        assert derive_tier(brewer) == 2

    def test_tier_2_profiling_temp(self):
        brewer = _make_brewer(temp_control_type="profiling")
        assert derive_tier(brewer) == 2

    def test_tier_3_timed_preinfusion(self):
        brewer = _make_brewer(preinfusion_type="timed")
        assert derive_tier(brewer) == 3

    def test_tier_3_adjustable_pressure_preinfusion(self):
        brewer = _make_brewer(preinfusion_type="adjustable_pressure")
        assert derive_tier(brewer) == 3

    def test_tier_3_programmable_preinfusion(self):
        brewer = _make_brewer(preinfusion_type="programmable")
        assert derive_tier(brewer) == 3

    def test_tier_4_manual_paddle(self):
        brewer = _make_brewer(flow_control_type="manual_paddle")
        assert derive_tier(brewer) == 4

    def test_tier_4_manual_valve(self):
        brewer = _make_brewer(flow_control_type="manual_valve")
        assert derive_tier(brewer) == 4

    def test_tier_4_manual_pressure_profiling(self):
        brewer = _make_brewer(pressure_control_type="manual_profiling")
        assert derive_tier(brewer) == 4

    def test_tier_4_programmable_pressure(self):
        brewer = _make_brewer(pressure_control_type="programmable")
        assert derive_tier(brewer) == 4

    def test_tier_5_programmable_flow(self):
        brewer = _make_brewer(flow_control_type="programmable")
        assert derive_tier(brewer) == 5

    def test_tier_5_overrides_lower_features(self):
        # Even with pid + preinfusion, programmable flow wins -> tier 5
        brewer = _make_brewer(
            flow_control_type="programmable",
            temp_control_type="pid",
            preinfusion_type="timed",
        )
        assert derive_tier(brewer) == 5

    def test_higher_tier_wins(self):
        # Tier 4 (manual_paddle) beats tier 3 (timed preinfusion)
        brewer = _make_brewer(
            flow_control_type="manual_paddle",
            preinfusion_type="timed",
            temp_control_type="pid",
        )
        assert derive_tier(brewer) == 4


class TestTierLabels:
    """Verify TIER_LABELS covers all tiers."""

    def test_all_tiers_labeled(self):
        assert set(TIER_LABELS.keys()) == {1, 2, 3, 4, 5}

    def test_label_values_are_strings(self):
        for label in TIER_LABELS.values():
            assert isinstance(label, str)
