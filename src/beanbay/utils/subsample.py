"""Maximin diversity subsampling for BayBE measurements."""

from __future__ import annotations

import numpy as np
import pandas as pd


def maximin_subsample(
    df: pd.DataFrame,
    param_cols: list[str],
    n: int,
) -> pd.DataFrame:
    """Subsample a DataFrame to n rows maximizing parameter space coverage.

    Uses greedy maximin distance selection: iteratively picks the row
    farthest (in normalized Euclidean distance) from the already-selected
    set. This preserves exploration diversity while discarding redundant
    measurements clustered around converged optima.

    Parameters
    ----------
    df : pd.DataFrame
        Measurements DataFrame with at least ``param_cols`` columns.
    param_cols : list[str]
        Column names to use for distance computation.
    n : int
        Target number of rows. If ``len(df) <= n``, returns ``df`` unchanged.

    Returns
    -------
    pd.DataFrame
        Subsampled DataFrame with at most ``n`` rows, preserving original index.
    """
    if len(df) <= n:
        return df

    X = df[param_cols].to_numpy(dtype=float, na_value=0.0)

    # Normalize to [0, 1] per column
    col_min = X.min(axis=0)
    col_range = X.max(axis=0) - col_min
    col_range[col_range == 0] = 1.0  # avoid division by zero for constant columns
    X_norm = (X - col_min) / col_range

    # Greedy maximin: start with the first row, iteratively pick farthest
    selected = [0]
    # min_dist[i] = min distance from row i to any selected row
    min_dist = np.full(len(X_norm), np.inf)

    for _ in range(n - 1):
        # Update min distances with the last selected point
        last = X_norm[selected[-1]]
        dists_to_last = np.sum((X_norm - last) ** 2, axis=1)
        min_dist = np.minimum(min_dist, dists_to_last)
        # Zero out already selected
        min_dist[selected] = -1
        # Pick the farthest point
        selected.append(int(np.argmax(min_dist)))

    return df.iloc[selected]
