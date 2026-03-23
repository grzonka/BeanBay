"""Parameter range computation service.

Provides the 3-layer effective range system and capability gate evaluation.
"""

from __future__ import annotations

import re
from typing import Any


def evaluate_requires(condition: str | None, brewer: Any) -> bool:
    """Evaluate a capability gate condition against a brewer.

    Supported formats:
    - ``"attr != value"``
    - ``"attr == value"`` (including ``"true"``/``"false"`` for booleans)
    - ``"attr in (val1, val2, ...)"``

    Parameters
    ----------
    condition : str | None
        Condition string, or None (always passes).
    brewer : Any
        Object with brewer capability attributes.

    Returns
    -------
    bool
        Whether the condition is satisfied.
    """
    if condition is None:
        return True

    condition = condition.strip()

    # "attr in (val1, val2, ...)"
    m = re.match(r"(\w+)\s+in\s+\(([^)]+)\)", condition)
    if m:
        attr, values_str = m.group(1), m.group(2)
        values = [v.strip() for v in values_str.split(",")]
        return str(getattr(brewer, attr, None)) in values

    # "attr != value"
    m = re.match(r"(\w+)\s*!=\s*(\w+)", condition)
    if m:
        attr, value = m.group(1), m.group(2)
        return str(getattr(brewer, attr, None)) != value

    # "attr == value"
    m = re.match(r"(\w+)\s*==\s*(\w+)", condition)
    if m:
        attr, value = m.group(1), m.group(2)
        actual = getattr(brewer, attr, None)
        if value.lower() == "true":
            return bool(actual) is True
        if value.lower() == "false":
            return bool(actual) is False
        return str(actual) == value

    return False
