"""Read schemas for stats endpoints."""

import uuid
from datetime import datetime

from sqlmodel import SQLModel


# ======================================================================
# Shared
# ======================================================================


class FlavorTagCount(SQLModel):
    """Flavor tag usage frequency."""

    flavor_tag_id: uuid.UUID
    flavor_tag_name: str
    count: int


class NamedUsageCount(SQLModel):
    """Entity ranked by brew usage count."""

    id: uuid.UUID
    name: str
    brew_count: int


# ======================================================================
# Brew Stats
# ======================================================================


class MethodBrewCount(SQLModel):
    """Brew count grouped by brew method."""

    brew_method_id: uuid.UUID
    brew_method_name: str
    count: int


class BrewStatsRead(SQLModel):
    """Aggregated brew statistics."""

    total: int
    this_week: int
    this_month: int
    total_failed: int
    fail_rate: float | None
    avg_dose_g: float | None
    avg_yield_g: float | None
    avg_brew_time_s: float | None
    last_brewed_at: datetime | None
    by_method: list[MethodBrewCount]


# ======================================================================
# Bean Stats
# ======================================================================


class RoasterBeanCount(SQLModel):
    """Bean count grouped by roaster."""

    roaster_id: uuid.UUID
    roaster_name: str
    count: int


class OriginBeanCount(SQLModel):
    """Bean count grouped by origin."""

    origin_id: uuid.UUID
    origin_name: str
    count: int


class BeanStatsRead(SQLModel):
    """Aggregated bean and bag statistics."""

    total_beans: int
    beans_active: int
    mix_type_breakdown: dict[str, int]
    use_type_breakdown: dict[str, int]
    top_roasters: list[RoasterBeanCount]
    top_origins: list[OriginBeanCount]

    total_bags: int
    bags_active: int
    bags_unopened: int
    avg_bag_weight_g: float | None
    avg_bag_price: float | None


# ======================================================================
# Taste Stats
# ======================================================================


class BrewTasteAxisAverages(SQLModel):
    """Average scores across all rated brews."""

    score: float | None
    acidity: float | None
    sweetness: float | None
    body: float | None
    bitterness: float | None
    balance: float | None
    aftertaste: float | None


class BeanTasteAxisAverages(SQLModel):
    """Average scores across all bean ratings."""

    score: float | None
    acidity: float | None
    sweetness: float | None
    body: float | None
    complexity: float | None
    aroma: float | None
    clean_cup: float | None


class BrewTasteStats(SQLModel):
    """Sensory stats from brew tastings."""

    total_rated: int
    avg_axes: BrewTasteAxisAverages
    best_score: float | None
    best_brew_id: uuid.UUID | None
    top_flavor_tags: list[FlavorTagCount]


class BeanTasteStats(SQLModel):
    """Sensory stats from bean ratings."""

    total_rated: int
    avg_axes: BeanTasteAxisAverages
    best_score: float | None
    best_bean_id: uuid.UUID | None
    top_flavor_tags: list[FlavorTagCount]


class TasteStatsRead(SQLModel):
    """Combined sensory statistics."""

    brew_taste: BrewTasteStats
    bean_taste: BeanTasteStats


# ======================================================================
# Equipment Stats
# ======================================================================


class SetupUsage(SQLModel):
    """Brew setup ranked by usage."""

    id: uuid.UUID
    name: str | None
    brew_count: int


class EquipmentStatsRead(SQLModel):
    """Aggregated equipment statistics and usage rankings."""

    total_grinders: int
    total_brewers: int
    total_papers: int
    total_waters: int

    top_grinders: list[NamedUsageCount]
    top_brewers: list[NamedUsageCount]
    top_setups: list[SetupUsage]

    most_used_method: NamedUsageCount | None


# ======================================================================
# Cupping Stats
# ======================================================================


class CuppingStatsRead(SQLModel):
    """Aggregated cupping session statistics."""

    total: int
    avg_total_score: float | None
    best_total_score: float | None
    best_cupping_id: uuid.UUID | None
    top_flavor_tags: list[FlavorTagCount]
