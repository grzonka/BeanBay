"""Tests for maximin diversity subsampling."""

import pandas as pd

from beanbay.utils.subsample import maximin_subsample


class TestMaximinSubsample:
    """Tests for maximin_subsample."""

    def test_returns_all_when_under_limit(self):
        """Returns full DataFrame when len(df) <= n."""
        df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6], "score": [7, 8, 9]})
        result = maximin_subsample(df, ["x", "y"], n=5)
        assert len(result) == 3

    def test_subsamples_to_n(self):
        """Returns exactly n rows when len(df) > n."""
        df = pd.DataFrame({"x": range(100), "y": range(100), "score": range(100)})
        result = maximin_subsample(df, ["x", "y"], n=10)
        assert len(result) == 10

    def test_picks_extremes(self):
        """Selects points at extremes of parameter space."""
        # Cluster of 50 points near origin + 2 outliers
        xs = [0.0] * 50 + [100.0, -100.0]
        ys = [0.0] * 50 + [100.0, -100.0]
        df = pd.DataFrame({"x": xs, "y": ys, "score": range(52)})
        result = maximin_subsample(df, ["x", "y"], n=5)
        # Both outliers must be selected
        assert 100.0 in result["x"].values
        assert -100.0 in result["x"].values

    def test_handles_constant_column(self):
        """Does not crash when a parameter column is constant."""
        df = pd.DataFrame({"x": [5.0] * 20, "y": range(20), "score": range(20)})
        result = maximin_subsample(df, ["x", "y"], n=5)
        assert len(result) == 5

    def test_preserves_all_columns(self):
        """Returned DataFrame has all original columns."""
        df = pd.DataFrame({"x": range(20), "y": range(20), "score": range(20), "extra": range(20)})
        result = maximin_subsample(df, ["x", "y"], n=5)
        assert list(result.columns) == ["x", "y", "score", "extra"]
