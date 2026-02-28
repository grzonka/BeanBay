"""Integration test: grinder bounds enforcement through full recommendation flow."""

import pytest

from app.models.equipment import Grinder
from app.services.optimizer import snap_grind_to_step
from app.services.parameter_registry import build_parameters_for_setup


class TestGrinderBoundsIntegration:
    """Test that grinder bounds are enforced end-to-end."""

    def test_build_params_clips_to_grinder(self):
        """build_parameters_for_setup clips grind_setting to grinder range."""
        grinder = Grinder(name="Small", display_format="decimal", ring_sizes=[[0, 18, 1]])
        params = build_parameters_for_setup("espresso", grinder=grinder)
        grind = next(p for p in params if p.name == "grind_setting")
        # Espresso default is (15, 25), grinder max is 18 -> should clip to (15, 18)
        assert grind.bounds.lower >= 0
        assert grind.bounds.upper <= 18

    def test_snap_respects_grinder_step(self):
        """snap_grind_to_step snaps to valid grinder steps."""
        grinder = Grinder(name="Stepped", display_format="decimal", ring_sizes=[[0, 40, 0.5]])
        assert snap_grind_to_step(17.3, grinder) == 17.5
        assert snap_grind_to_step(17.1, grinder) == 17.0

    def test_multi_ring_display_roundtrip(self):
        """Multi-ring grinder display format roundtrips correctly."""
        grinder = Grinder(
            name="X-Ultra", display_format="x.y.z",
            ring_sizes=[[0, 4, 1], [0, 5, 1], [0, 10, 1]]
        )
        # to_display and from_display are inverses
        for linear in range(330):
            display = grinder.to_display(float(linear))
            back = grinder.from_display(display)
            assert back == float(linear), f"Roundtrip failed for {linear}: {display} -> {back}"

    def test_grinder_bounds_with_bean_overrides(self):
        """Grinder bounds are a hard ceiling even with wider bean overrides."""
        grinder = Grinder(name="Narrow", display_format="decimal", ring_sizes=[[0, 20, 1]])
        overrides = {"grind_setting": {"min": 5.0, "max": 30.0}}
        params = build_parameters_for_setup("espresso", grinder=grinder, overrides=overrides)
        grind = next(p for p in params if p.name == "grind_setting")
        assert grind.bounds.upper <= 20.0  # Grinder caps it

    def test_no_grinder_preserves_defaults(self):
        """Without grinder, espresso defaults are preserved."""
        params = build_parameters_for_setup("espresso")
        grind = next(p for p in params if p.name == "grind_setting")
        assert grind.bounds.lower == 15.0
        assert grind.bounds.upper == 25.0
