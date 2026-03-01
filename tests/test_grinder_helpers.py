"""Tests for Grinder helper methods: linear_bounds, finest_step, to_display, from_display."""

import pytest

from app.models.equipment import Grinder


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def continuous_grinder():
    """Single-ring continuous grinder (0-50, stepless)."""
    return Grinder(
        name="Niche Zero",
        display_format="decimal",
        ring_sizes=[(0, 50, None)],
    )


@pytest.fixture()
def stepped_grinder():
    """Single-ring stepped grinder (0-40, step=1)."""
    return Grinder(
        name="Eureka Mignon",
        display_format="decimal",
        ring_sizes=[(0, 40, 1)],
    )


@pytest.fixture()
def half_step_grinder():
    """Single-ring stepped grinder with half-steps (0-20, step=0.5)."""
    return Grinder(
        name="Half-Step Grinder",
        display_format="decimal",
        ring_sizes=[(0, 20, 0.5)],
    )


@pytest.fixture()
def two_ring_grinder():
    """Two-ring grinder X.Y: X in 0-30, Y in 0-9."""
    return Grinder(
        name="Lagom P64",
        display_format="x.y",
        ring_sizes=[(0, 30, 1), (0, 9, 1)],
    )


@pytest.fixture()
def three_ring_grinder():
    """Three-ring grinder X.Y.Z: X in 0-4, Y in 0-5, Z in 0-10."""
    return Grinder(
        name="Commandante C40",
        display_format="x.y.z",
        ring_sizes=[(0, 4, 1), (0, 5, 1), (0, 10, 1)],
    )


# ---------------------------------------------------------------------------
# TestLinearBounds
# ---------------------------------------------------------------------------

class TestLinearBounds:
    """Tests for Grinder.linear_bounds()."""

    def test_single_ring_continuous(self, continuous_grinder):
        assert continuous_grinder.linear_bounds() == (0.0, 50.0)

    def test_single_ring_stepped(self, stepped_grinder):
        assert stepped_grinder.linear_bounds() == (0.0, 40.0)

    def test_two_rings(self, two_ring_grinder):
        # 31 * 10 = 310 positions, linear range 0-309
        assert two_ring_grinder.linear_bounds() == (0.0, 309.0)

    def test_three_rings(self, three_ring_grinder):
        # 5 * 6 * 11 = 330 positions, linear range 0-329
        assert three_ring_grinder.linear_bounds() == (0.0, 329.0)

    def test_none_ring_sizes(self):
        g = Grinder(name="Unknown")
        assert g.linear_bounds() is None


# ---------------------------------------------------------------------------
# TestFinestStep
# ---------------------------------------------------------------------------

class TestFinestStep:
    """Tests for Grinder.finest_step()."""

    def test_continuous_returns_none(self, continuous_grinder):
        assert continuous_grinder.finest_step() is None

    def test_single_stepped(self, stepped_grinder):
        assert stepped_grinder.finest_step() == 1.0

    def test_multi_ring(self, three_ring_grinder):
        assert three_ring_grinder.finest_step() == 1.0

    def test_half_step_decimal(self, half_step_grinder):
        assert half_step_grinder.finest_step() == 0.5


# ---------------------------------------------------------------------------
# TestToDisplay
# ---------------------------------------------------------------------------

class TestToDisplay:
    """Tests for Grinder.to_display(value)."""

    def test_decimal_continuous(self, continuous_grinder):
        assert continuous_grinder.to_display(25.3) == "25.3"

    def test_decimal_stepped_whole(self, stepped_grinder):
        # Whole numbers should not show trailing .0
        assert stepped_grinder.to_display(28.0) == "28"

    def test_two_rings(self, two_ring_grinder):
        # 15*10 + 5 = 155
        assert two_ring_grinder.to_display(155.0) == "15.5"

    def test_three_rings(self, three_ring_grinder):
        # 2*66 + 3*11 + 7 = 132+33+7 = 172
        assert three_ring_grinder.to_display(172.0) == "2.3.7"

    def test_three_rings_zero(self, three_ring_grinder):
        assert three_ring_grinder.to_display(0.0) == "0.0.0"

    def test_three_rings_max(self, three_ring_grinder):
        # 4*66 + 5*11 + 10 = 264+55+10 = 329
        assert three_ring_grinder.to_display(329.0) == "4.5.10"


# ---------------------------------------------------------------------------
# TestFromDisplay
# ---------------------------------------------------------------------------

class TestFromDisplay:
    """Tests for Grinder.from_display(text)."""

    def test_decimal(self, continuous_grinder):
        assert continuous_grinder.from_display("25.3") == 25.3

    def test_decimal_stepped(self, stepped_grinder):
        assert stepped_grinder.from_display("28") == 28.0

    def test_two_rings(self, two_ring_grinder):
        # 15*10 + 5 = 155
        assert two_ring_grinder.from_display("15.5") == 155.0

    def test_three_rings(self, three_ring_grinder):
        # 2*66 + 3*11 + 7 = 172
        assert three_ring_grinder.from_display("2.3.7") == 172.0

    def test_roundtrip_two_rings(self, two_ring_grinder):
        """Every valid linear value should round-trip through display notation."""
        for linear in range(310):  # 0-309
            displayed = two_ring_grinder.to_display(float(linear))
            recovered = two_ring_grinder.from_display(displayed)
            assert recovered == float(linear), (
                f"Roundtrip failed for linear={linear}: "
                f"to_display={displayed}, from_display={recovered}"
            )

    def test_roundtrip_three_rings(self, three_ring_grinder):
        """Every valid linear value should round-trip through display notation."""
        for linear in range(330):  # 0-329
            displayed = three_ring_grinder.to_display(float(linear))
            recovered = three_ring_grinder.from_display(displayed)
            assert recovered == float(linear), (
                f"Roundtrip failed for linear={linear}: "
                f"to_display={displayed}, from_display={recovered}"
            )


# ---------------------------------------------------------------------------
# TestRingSizesProperty
# ---------------------------------------------------------------------------

class TestRingSizesProperty:
    """Tests for the ring_sizes JSON property pattern."""

    def test_set_via_constructor(self, two_ring_grinder):
        assert two_ring_grinder.ring_sizes == [(0, 30, 1), (0, 9, 1)]

    def test_set_via_property(self):
        g = Grinder(name="Test")
        g.ring_sizes = [(0, 50, None)]
        assert g.ring_sizes == [(0, 50, None)]

    def test_none_by_default(self):
        g = Grinder(name="Test")
        assert g.ring_sizes is None

    def test_json_roundtrip(self):
        """Setting ring_sizes stores JSON and retrieves the same structure."""
        rings = [(0, 4, 1), (0, 5, 1), (0, 10, 1)]
        g = Grinder(name="Test", ring_sizes=rings)
        # Access the raw JSON column to verify serialization
        import json
        raw = json.loads(g.ring_sizes_json)
        assert raw == [[0, 4, 1], [0, 5, 1], [0, 10, 1]]
        # Property should convert back to tuples
        assert g.ring_sizes == [(0, 4, 1), (0, 5, 1), (0, 10, 1)]


# ---------------------------------------------------------------------------
# TestDisplayFormat
# ---------------------------------------------------------------------------

class TestDisplayFormat:
    """Tests for the display_format column."""

    def test_default_display_format(self):
        g = Grinder(name="Test")
        assert g.display_format == "decimal"

    def test_set_display_format(self):
        g = Grinder(name="Test", display_format="x.y.z")
        assert g.display_format == "x.y.z"
