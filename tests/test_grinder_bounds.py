"""Tests for grinder bounds enforcement (Task 4), step snapping (Task 5), and fingerprint (Task 9).

Covers:
  - Grind setting bounds clipped to grinder's physical range
  - Bean overrides + grinder constraint interaction
  - snap_grind_to_step for continuous, stepped, half-step, and multi-ring grinders
  - Clamping to grinder bounds
  - No-grinder passthrough
  - Campaign fingerprint changes when grinder bounds change
"""

from app.models.equipment import Grinder
from app.services.optimizer import _bounds_fingerprint, _resolve_bounds, snap_grind_to_step
from app.services.parameter_registry import build_parameters_for_setup


# ===========================================================================
# Task 4: Bounds Enforcement in Optimizer
# ===========================================================================


def test_grind_setting_clipped_to_grinder_range():
    """If grinder max is 18, grind_setting bounds should not exceed 18."""
    grinder = Grinder(name="Small", display_format="decimal", ring_sizes=[[0, 18, 1]])
    params = build_parameters_for_setup("espresso", grinder=grinder)
    grind_param = next(p for p in params if p.name == "grind_setting")
    assert grind_param.bounds.upper <= 18.0
    assert grind_param.bounds.lower >= 0.0


def test_grind_setting_clipped_preserves_method_lower_bound():
    """If grinder range wider than method default, use method default."""
    grinder = Grinder(name="Wide", display_format="decimal", ring_sizes=[[0, 100, None]])
    params = build_parameters_for_setup("espresso", grinder=grinder)
    grind_param = next(p for p in params if p.name == "grind_setting")
    assert grind_param.bounds.lower == 15.0  # espresso default
    assert grind_param.bounds.upper == 25.0  # espresso default


def test_grind_setting_with_override_and_grinder():
    """Bean override + grinder constraint: grinder is hard ceiling."""
    grinder = Grinder(name="G", display_format="decimal", ring_sizes=[[0, 20, 0.5]])
    overrides = {"grind_setting": {"min": 10.0, "max": 25.0}}
    params = build_parameters_for_setup("espresso", grinder=grinder, overrides=overrides)
    grind_param = next(p for p in params if p.name == "grind_setting")
    assert grind_param.bounds.lower == 10.0
    assert grind_param.bounds.upper == 20.0  # Clipped from 25 to grinder max


def test_no_grinder_uses_defaults():
    """Without a grinder, default bounds are used."""
    params = build_parameters_for_setup("espresso")
    grind_param = next(p for p in params if p.name == "grind_setting")
    assert grind_param.bounds.lower == 15.0
    assert grind_param.bounds.upper == 25.0


# ===========================================================================
# Task 5: Post-Recommendation Step Snapping
# ===========================================================================


class TestSnapGrindToStep:
    def test_continuous_no_snap(self):
        grinder = Grinder(name="Niche", display_format="decimal", ring_sizes=[[0, 50, None]])
        assert snap_grind_to_step(25.3, grinder) == 25.3

    def test_stepped_snaps_to_nearest(self):
        grinder = Grinder(name="C40", display_format="decimal", ring_sizes=[[0, 40, 1]])
        assert snap_grind_to_step(25.3, grinder) == 25.0
        assert snap_grind_to_step(25.7, grinder) == 26.0

    def test_half_step_snaps(self):
        grinder = Grinder(name="G1", display_format="decimal", ring_sizes=[[0, 40, 0.5]])
        assert snap_grind_to_step(25.3, grinder) == 25.5
        assert snap_grind_to_step(25.1, grinder) == 25.0

    def test_multi_ring_snaps_to_integer(self):
        grinder = Grinder(name="Sette", display_format="x.y", ring_sizes=[[0, 30, 1], [0, 9, 1]])
        assert snap_grind_to_step(155.4, grinder) == 155.0
        assert snap_grind_to_step(155.6, grinder) == 156.0

    def test_clamps_to_bounds(self):
        grinder = Grinder(name="C40", display_format="decimal", ring_sizes=[[0, 40, 1]])
        assert snap_grind_to_step(-1.0, grinder) == 0.0
        assert snap_grind_to_step(41.0, grinder) == 40.0

    def test_no_grinder_returns_value(self):
        assert snap_grind_to_step(25.3, None) == 25.3


# ===========================================================================
# Task 9: Campaign Fingerprint Includes Grinder Bounds
# ===========================================================================


def test_fingerprint_changes_when_grinder_bounds_change():
    """Different grinder ranges should produce different fingerprints."""
    grinder_a = Grinder(name="A", display_format="decimal", ring_sizes=[[0, 40, 1]])
    grinder_b = Grinder(name="B", display_format="decimal", ring_sizes=[[0, 18, 1]])

    fp_a = _bounds_fingerprint(_resolve_bounds(None, "espresso", grinder=grinder_a))
    fp_b = _bounds_fingerprint(_resolve_bounds(None, "espresso", grinder=grinder_b))
    assert fp_a != fp_b, "Different grinder ranges should produce different fingerprints"


def test_fingerprint_same_when_same_grinder():
    """Same grinder should produce identical fingerprints."""
    grinder = Grinder(name="A", display_format="decimal", ring_sizes=[[0, 40, 1]])
    fp_1 = _bounds_fingerprint(_resolve_bounds(None, "espresso", grinder=grinder))
    fp_2 = _bounds_fingerprint(_resolve_bounds(None, "espresso", grinder=grinder))
    assert fp_1 == fp_2


def test_resolve_bounds_clips_grind_to_grinder():
    """_resolve_bounds should clip grind_setting to grinder's physical range."""
    grinder = Grinder(name="Narrow", display_format="decimal", ring_sizes=[[0, 18, 1]])
    bounds = _resolve_bounds(None, "espresso", grinder=grinder)
    # Espresso default grind is (15, 25), grinder max is 18 -> (15, 18)
    assert bounds["grind_setting"] == (15.0, 18.0)


def test_resolve_bounds_no_grinder_preserves_defaults():
    """Without a grinder, _resolve_bounds should return unclipped defaults."""
    bounds = _resolve_bounds(None, "espresso")
    assert bounds["grind_setting"] == (15.0, 25.0)
