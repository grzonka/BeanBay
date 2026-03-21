"""Grinder dial display conversion utilities.

Standalone functions for converting between canonical linear grind values
and human-readable display notation (e.g., ``"2.5.1"`` for multi-ring dials).

Adapted from the ``Grinder`` ORM model on the main branch (original author: grzonka).
"""

from __future__ import annotations


def ring_position_counts(ring_sizes: list[tuple[float, float, float | None]]) -> list[int]:
    """Compute the number of discrete positions per ring.

    Parameters
    ----------
    ring_sizes : list[tuple[float, float, float | None]]
        List of ``(min, max, step)`` tuples per ring.  *step* may be ``None``
        for continuous rings, in which case it is treated as 1.

    Returns
    -------
    list[int]
        Number of discrete positions for each ring: ``int(max - min + 1)``.
    """
    return [int(r[1] - r[0] + 1) for r in ring_sizes]


def linear_bounds(
    ring_sizes: list[tuple[float, float, float | None]],
) -> tuple[float, float] | None:
    """Compute linearised ``(min, max)`` bounds from a ring configuration.

    Parameters
    ----------
    ring_sizes : list[tuple[float, float, float | None]]
        List of ``(min, max, step)`` tuples per ring.

    Returns
    -------
    tuple[float, float] | None
        ``(min, max)`` for the linearised grind space, or ``None`` when
        *ring_sizes* is empty.

    Notes
    -----
    * Single ring: the linear range equals the ring's own ``(min, max)``.
    * Multi-ring: the linear range is ``(0, total_positions - 1)`` where
      ``total_positions`` is the product of all per-ring position counts.
    """
    if not ring_sizes:
        return None

    if len(ring_sizes) == 1:
        return (float(ring_sizes[0][0]), float(ring_sizes[0][1]))

    counts = ring_position_counts(ring_sizes)
    total = 1
    for c in counts:
        total *= c
    return (0.0, float(total - 1))


def to_display(value: float, ring_sizes: list[tuple[float, float, float | None]]) -> str:
    """Convert a canonical linear value to display notation.

    Parameters
    ----------
    value : float
        The linear grind setting value.
    ring_sizes : list[tuple[float, float, float | None]]
        List of ``(min, max, step)`` tuples per ring.

    Returns
    -------
    str
        Human-readable dial string.  Single-ring grinders return a plain
        number (e.g., ``"22"`` or ``"15.5"``).  Multi-ring grinders return
        dot-separated per-ring positions (e.g., ``"2.5.1"``).

    Notes
    -----
    Multi-ring decomposition uses mixed-radix arithmetic with the most
    significant ring first.
    """
    if not ring_sizes:
        return str(value)

    if len(ring_sizes) == 1:
        step = ring_sizes[0][2]
        if step is not None and value == int(value):
            return str(int(value))
        return str(value)

    # Multi-ring: mixed-radix decomposition (most significant ring first)
    counts = ring_position_counts(ring_sizes)
    linear_int = int(value)
    parts: list[int] = []
    for i in range(len(counts) - 1, -1, -1):
        parts.append(linear_int % counts[i])
        linear_int //= counts[i]
    parts.reverse()

    # Add ring minimums to each position
    result = [str(parts[i] + int(ring_sizes[i][0])) for i in range(len(ring_sizes))]
    return ".".join(result)


def from_display(text: str, ring_sizes: list[tuple[float, float, float | None]]) -> float:
    """Parse display notation to a canonical linear value.

    Parameters
    ----------
    text : str
        The display string, e.g. ``"22"`` or ``"2.5.1"``.
    ring_sizes : list[tuple[float, float, float | None]]
        List of ``(min, max, step)`` tuples per ring.

    Returns
    -------
    float
        The canonical linear value.
    """
    if not ring_sizes:
        return float(text)

    if len(ring_sizes) == 1:
        return float(text)

    # Multi-ring: parse parts and compute linear value
    parts = text.split(".")
    counts = ring_position_counts(ring_sizes)
    linear = 0
    for i, part_str in enumerate(parts):
        position = int(part_str) - int(ring_sizes[i][0])  # subtract ring minimum
        # Multiply by product of all subsequent ring counts
        multiplier = 1
        for j in range(i + 1, len(counts)):
            multiplier *= counts[j]
        linear += position * multiplier
    return float(linear)
