import json
import uuid
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String, Table, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


# Valid values for brewer capability enums
TEMP_CONTROL_TYPES = ("none", "preset", "pid", "profiling")
PREINFUSION_TYPES = ("none", "fixed", "timed", "adjustable_pressure", "programmable", "manual")
PRESSURE_CONTROL_TYPES = (
    "fixed",
    "opv_adjustable",
    "electronic",
    "manual_profiling",
    "programmable",
)
FLOW_CONTROL_TYPES = ("none", "manual_paddle", "manual_valve", "programmable")
STOP_MODES = ("manual", "timed", "volumetric", "gravimetric")


# Association table for Brewer <-> BrewMethod many-to-many relationship
brewer_methods = Table(
    "brewer_methods",
    Base.metadata,
    Column("brewer_id", String, ForeignKey("brewers.id"), primary_key=True),
    Column("method_id", String, ForeignKey("brew_methods.id"), primary_key=True),
)


class Grinder(Base):
    __tablename__ = "grinders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)

    # ── Multi-ring grind dial columns ───────────────────────────────────
    display_format = Column(String, nullable=False, default="decimal")
    # Dial notation: "decimal", "x.y", "x.y.z"

    ring_sizes_json = Column(Text, nullable=True)
    # JSON-serialized list of [min, max, step] tuples per ring.
    # step=None for continuous.  Example: [[0, 50, null]] or [[0, 4, 1], [0, 5, 1], [0, 10, 1]]

    is_retired = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())

    def __init__(self, **kwargs):
        # Handle ring_sizes convenience kwarg -> serialize to ring_sizes_json
        ring_sizes = kwargs.pop("ring_sizes", None)
        # Set Python-side defaults for new columns
        kwargs.setdefault("display_format", "decimal")
        super().__init__(**kwargs)
        if ring_sizes is not None:
            self.ring_sizes = ring_sizes

    # ── ring_sizes JSON property ─────────────────────────────────────────

    @property
    def ring_sizes(self) -> Optional[list[tuple]]:
        """Deserialize ring_sizes_json into a list of (min, max, step) tuples."""
        if self.ring_sizes_json is None:
            return None
        raw = json.loads(self.ring_sizes_json)
        return [tuple(r) for r in raw]

    @ring_sizes.setter
    def ring_sizes(self, value: Optional[list]) -> None:
        """Serialize a list of (min, max, step) tuples to JSON."""
        if value is None:
            self.ring_sizes_json = None
        else:
            self.ring_sizes_json = json.dumps([list(r) for r in value])

    # ── Helper methods ───────────────────────────────────────────────────

    def _ring_position_counts(self) -> list[int]:
        """Number of discrete positions per ring: max - min + 1 (for stepped rings)."""
        rings = self.ring_sizes
        if rings is None:
            return []
        return [int(r[1] - r[0] + 1) for r in rings]

    def linear_bounds(self) -> Optional[tuple[float, float]]:
        """Compute linearized (min, max) from ring_sizes.

        For a single continuous ring, returns (ring_min, ring_max).
        For multi-ring or single stepped ring, returns (0, total_positions - 1).
        Returns None if ring_sizes is not set.
        """
        rings = self.ring_sizes
        if rings is None:
            return None

        if len(rings) == 1:
            # Single ring: linear range equals the ring's own range
            return (float(rings[0][0]), float(rings[0][1]))

        # Multi-ring: total positions = product of per-ring position counts
        counts = self._ring_position_counts()
        total = 1
        for c in counts:
            total *= c
        return (0.0, float(total - 1))

    def finest_step(self) -> Optional[float]:
        """Return the smallest step size across all rings, or None if any ring is continuous."""
        rings = self.ring_sizes
        if rings is None:
            return None
        steps = [r[2] for r in rings]
        if any(s is None for s in steps):
            return None
        return float(min(steps))

    def to_display(self, value: float) -> str:
        """Convert a linear value to display notation.

        For decimal format (single ring): returns str(value), dropping .0 for whole numbers
        when the ring is stepped.
        For multi-ring formats (x.y, x.y.z): decomposes the linear integer into
        per-ring positions using mixed-radix decomposition.
        """
        rings = self.ring_sizes
        if rings is None:
            return str(value)

        if len(rings) == 1:
            # Single ring — decimal display
            step = rings[0][2]
            if step is not None and value == int(value):
                return str(int(value))
            return str(value)

        # Multi-ring: mixed-radix decomposition (most significant ring first)
        counts = self._ring_position_counts()
        linear_int = int(value)
        parts: list[int] = []
        for i in range(len(counts) - 1, -1, -1):
            parts.append(linear_int % counts[i])
            linear_int //= counts[i]
        parts.reverse()

        # Add ring minimums to each position
        result = [str(parts[i] + int(rings[i][0])) for i in range(len(rings))]
        return ".".join(result)

    def from_display(self, text: str) -> float:
        """Parse display notation to a linear value.

        For decimal format (single ring): parses as float.
        For multi-ring formats: computes linear value from per-ring positions.
        """
        rings = self.ring_sizes
        if rings is None:
            return float(text)

        if len(rings) == 1:
            return float(text)

        # Multi-ring: parse parts and compute linear value
        parts = text.split(".")
        counts = self._ring_position_counts()
        linear = 0
        for i, part_str in enumerate(parts):
            position = int(part_str) - int(rings[i][0])  # subtract ring minimum
            # Multiply by product of all subsequent ring counts
            multiplier = 1
            for j in range(i + 1, len(counts)):
                multiplier *= counts[j]
            linear += position * multiplier
        return float(linear)


class Brewer(Base):
    __tablename__ = "brewers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    is_retired = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())

    # ── Capability flags ─────────────────────────────────────────────────
    # Temperature capabilities
    temp_control_type = Column(String, nullable=False, default="pid")
    # Values: "none", "preset", "pid", "profiling"
    temp_min = Column(Float, nullable=True)  # °C — null means no settable range
    temp_max = Column(Float, nullable=True)  # °C
    temp_step = Column(Float, nullable=True)  # Resolution in °C (e.g., 0.5, 1.0)

    # Pre-infusion capabilities
    preinfusion_type = Column(String, nullable=False, default="none")
    # Values: "none", "fixed", "timed", "adjustable_pressure", "programmable", "manual"
    preinfusion_max_time = Column(Float, nullable=True)  # seconds

    # Pressure capabilities
    pressure_control_type = Column(String, nullable=False, default="fixed")
    # Values: "fixed", "opv_adjustable", "electronic", "manual_profiling", "programmable"
    pressure_min = Column(Float, nullable=True)  # bar
    pressure_max = Column(Float, nullable=True)  # bar

    # Flow capabilities
    flow_control_type = Column(String, nullable=False, default="none")
    # Values: "none", "manual_paddle", "manual_valve", "programmable"
    saturation_flow_rate = Column(Float, nullable=True)
    # ml/s — fixed brewer-level setting for saturation flow rate (e.g., 1.5 for Sage DB slayer mod)

    # Bloom capability
    has_bloom = Column(Boolean, nullable=False, default=False)

    # Stop mode
    stop_mode = Column(String, nullable=False, default="manual")
    # Values: "manual", "timed", "volumetric", "gravimetric"

    methods = relationship("BrewMethod", secondary="brewer_methods", backref="brewers")

    def __init__(self, **kwargs):
        # Set Python-side defaults so attributes are accessible before DB flush
        kwargs.setdefault("temp_control_type", "pid")
        kwargs.setdefault("preinfusion_type", "none")
        kwargs.setdefault("pressure_control_type", "fixed")
        kwargs.setdefault("flow_control_type", "none")
        kwargs.setdefault("has_bloom", False)
        kwargs.setdefault("stop_mode", "manual")
        super().__init__(**kwargs)


class Paper(Base):
    __tablename__ = "papers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_retired = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())


class WaterRecipe(Base):
    __tablename__ = "water_recipes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    recipe_details = Column(String, nullable=True)
    notes = Column(String, nullable=True)  # how it was made
    gh = Column(Float, nullable=True)  # General Hardness
    kh = Column(Float, nullable=True)  # Carbonate Hardness
    ca = Column(Float, nullable=True)  # Calcium
    mg = Column(Float, nullable=True)  # Magnesium
    na = Column(Float, nullable=True)  # Sodium
    cl = Column(Float, nullable=True)  # Chloride
    so4 = Column(Float, nullable=True)  # Sulfate
    is_retired = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())
