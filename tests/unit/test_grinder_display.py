"""Unit tests for grinder display conversion utilities."""

from __future__ import annotations

import pytest

from beanbay.utils.grinder_display import (
    from_display,
    linear_bounds,
    ring_position_counts,
    to_display,
)

# ── Ring configurations ──────────────────────────────────────────────────────

COMANDANTE_RINGS: list[tuple] = [(0, 40, 1)]  # Single stepped
NICHE_ZERO_RINGS: list[tuple] = [(0, 50, 0.5)]  # Single stepless (0.5 step)
JX_PRO_RINGS: list[tuple] = [(0, 4, 1), (0, 9, 1), (0, 3, 1)]  # 3-ring, 5*10*4=200 positions


# ── ring_position_counts ─────────────────────────────────────────────────────


class TestRingPositionCounts:
    """Tests for ring_position_counts."""

    def test_single_ring(self):
        assert ring_position_counts(COMANDANTE_RINGS) == [41]

    def test_multi_ring(self):
        assert ring_position_counts(JX_PRO_RINGS) == [5, 10, 4]

    def test_empty(self):
        assert ring_position_counts([]) == []


# ── linear_bounds ────────────────────────────────────────────────────────────


class TestLinearBounds:
    """Tests for linear_bounds."""

    def test_single_ring(self):
        assert linear_bounds(COMANDANTE_RINGS) == (0.0, 40.0)

    def test_single_ring_stepless(self):
        assert linear_bounds(NICHE_ZERO_RINGS) == (0.0, 50.0)

    def test_multi_ring(self):
        # 5 * 10 * 4 = 200 positions -> (0, 199)
        assert linear_bounds(JX_PRO_RINGS) == (0.0, 199.0)

    def test_empty(self):
        assert linear_bounds([]) is None


# ── to_display ───────────────────────────────────────────────────────────────


class TestToDisplay:
    """Tests for to_display."""

    def test_single_ring_stepped_whole(self):
        # Comandante: integer value displays without decimal
        assert to_display(22, COMANDANTE_RINGS) == "22"

    def test_single_ring_stepped_zero(self):
        assert to_display(0, COMANDANTE_RINGS) == "0"

    def test_single_ring_stepped_max(self):
        assert to_display(40, COMANDANTE_RINGS) == "40"

    def test_single_ring_stepless(self):
        # Niche Zero: half-step value keeps decimal
        assert to_display(15.5, NICHE_ZERO_RINGS) == "15.5"

    def test_single_ring_stepless_whole(self):
        # Niche Zero: whole number with 0.5 step still drops .0
        assert to_display(15.0, NICHE_ZERO_RINGS) == "15"

    def test_multi_ring_decomposition(self):
        # 101 = 2*40 + 5*4 + 1  -> "2.5.1"
        assert to_display(101, JX_PRO_RINGS) == "2.5.1"

    def test_multi_ring_zero(self):
        assert to_display(0, JX_PRO_RINGS) == "0.0.0"

    def test_multi_ring_max(self):
        # Max = 199 = 4*40 + 9*4 + 3 -> "4.9.3"
        assert to_display(199, JX_PRO_RINGS) == "4.9.3"

    def test_multi_ring_single_tick(self):
        # 1 -> "0.0.1"
        assert to_display(1, JX_PRO_RINGS) == "0.0.1"

    def test_empty_ring_sizes(self):
        assert to_display(42.5, []) == "42.5"


# ── from_display ─────────────────────────────────────────────────────────────


class TestFromDisplay:
    """Tests for from_display."""

    def test_single_ring_integer(self):
        assert from_display("22", COMANDANTE_RINGS) == 22.0

    def test_single_ring_float(self):
        assert from_display("15.5", NICHE_ZERO_RINGS) == 15.5

    def test_multi_ring(self):
        assert from_display("2.5.1", JX_PRO_RINGS) == 101.0

    def test_multi_ring_zero(self):
        assert from_display("0.0.0", JX_PRO_RINGS) == 0.0

    def test_multi_ring_max(self):
        assert from_display("4.9.3", JX_PRO_RINGS) == 199.0

    def test_empty_ring_sizes(self):
        assert from_display("42.5", []) == 42.5


# ── Round-trip ───────────────────────────────────────────────────────────────


class TestRoundTrip:
    """Verify that to_display/from_display round-trip correctly."""

    @pytest.mark.parametrize("value", [0, 10, 22, 40])
    def test_single_ring_roundtrip(self, value: int):
        assert from_display(to_display(value, COMANDANTE_RINGS), COMANDANTE_RINGS) == float(value)

    @pytest.mark.parametrize("value", [0, 1, 50, 101, 150, 199])
    def test_multi_ring_roundtrip(self, value: int):
        assert from_display(to_display(value, JX_PRO_RINGS), JX_PRO_RINGS) == float(value)

    def test_stepless_roundtrip(self):
        for v in [0.0, 0.5, 15.5, 25.0, 50.0]:
            assert from_display(to_display(v, NICHE_ZERO_RINGS), NICHE_ZERO_RINGS) == v
