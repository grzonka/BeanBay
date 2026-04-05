# Stats Endpoints Design

## Overview

Add five aggregated statistics sub-endpoints under `/api/v1/stats/` to power
independent dashboard widgets. Each endpoint returns a focused Pydantic response
model with metrics that are expensive or impossible to compute client-side
efficiently.

All endpoints return **200** on success. The router uses `tags=["stats"]`.

## Endpoints

| Endpoint | Person-scoped | Description |
|---|---|---|
| `GET /stats/brews` | Yes | Brew counts, averages, failure rate, method breakdown |
| `GET /stats/beans` | No | Bean/bag counts, enum breakdowns, top roasters/origins |
| `GET /stats/taste` | Yes | Sensory averages, best scores, flavor tag frequency |
| `GET /stats/equipment` | No | Equipment totals, usage rankings |
| `GET /stats/cuppings` | Yes | Cupping counts, score averages, flavor tags |

## Soft-Delete Convention

All queries exclude soft-deleted records (`retired_at IS NULL`) unless
explicitly noted otherwise. This applies to brews, beans, bags, equipment,
cuppings, ratings, and their taste sub-resources.

Flavor tag frequency counts include historically linked tags regardless of the
tag's own `retired_at` status — a retired tag that was used 50 times still
appears in the frequency list. This reflects actual usage history.

## Person Resolution Dependency

A shared `Annotated` dependency in `dependencies.py`, following the existing
`SessionDep` pattern. Synchronous to match the rest of the codebase:

```python
def _resolve_person_id(
    session: SessionDep,
    person_id: uuid.UUID | None = Query(default=None),
) -> uuid.UUID | None:
    if person_id:
        person = session.get(Person, person_id)
        if not person or person.retired_at:
            raise HTTPException(404, "Person not found")
        return person_id
    default = session.exec(select(Person).where(Person.is_default == True)).first()
    return default.id if default else None

OptionalPersonIdDep = Annotated[uuid.UUID | None, Depends(_resolve_person_id)]
```

Person-scoped endpoints (`/stats/brews`, `/stats/taste`, `/stats/cuppings`)
accept an optional `person_id` query parameter. When omitted, the default
person is used. Beans and equipment endpoints skip this dependency entirely.

## Response Models

All models live in `src/beanbay/schemas/stats.py`.

### Shared Models

```python
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
```

### GET /stats/brews

Query params: `person_id` (optional UUID, defaults to default person).

```python
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
    fail_rate: float | None          # total_failed / total, None if no brews
    avg_dose_g: float | None
    avg_yield_g: float | None
    avg_brew_time_s: float | None
    last_brewed_at: datetime | None
    by_method: list[MethodBrewCount]  # sorted desc by count
```

Queries: `COUNT`, `AVG`, `MAX` on non-retired brews (`retired_at IS NULL`)
with optional `person_id` WHERE clause. `by_method` joins
`brew → brew_setup → brew_method` with GROUP BY. `this_week`/`this_month` use
server-side UTC boundaries.

### GET /stats/beans

No query params (global).

```python
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
    # Beans (non-retired only)
    total_beans: int                         # COUNT WHERE retired_at IS NULL
    beans_active: int                        # non-retired with >= 1 non-retired bag
    mix_type_breakdown: dict[str, int]       # {"single_origin": 3, "blend": 1, ...}
    use_type_breakdown: dict[str, int]       # {"filter": 5, "espresso": 2, ...}
    top_roasters: list[RoasterBeanCount]     # sorted desc by count, all roasters
    top_origins: list[OriginBeanCount]       # sorted desc by count, all origins

    # Bags (non-retired only)
    total_bags: int                          # COUNT WHERE retired_at IS NULL
    bags_active: int                         # non-retired
    bags_unopened: int                       # active bags where opened_at is None
    avg_bag_weight_g: float | None
    avg_bag_price: float | None
```

Enum breakdown dict keys use the `StrEnum` `.value` strings (lowercase):
`"single_origin"`, `"blend"`, `"unknown"` for mix type; `"filter"`,
`"espresso"`, `"omni"` for use type.

`beans_active` uses EXISTS subquery for non-retired beans with at least one
non-retired bag. Breakdowns are GROUP BY on enum columns. Top roasters/origins
join through FK and M2M respectively.

### GET /stats/taste

Query params: `person_id` (optional UUID, defaults to default person).

```python
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
    total_rated: int                          # brews that have a BrewTaste
    avg_axes: BrewTasteAxisAverages
    best_score: float | None
    best_brew_id: uuid.UUID | None            # reference to the top-scoring brew
    top_flavor_tags: list[FlavorTagCount]      # sorted desc by count

class BeanTasteStats(SQLModel):
    """Sensory stats from bean ratings."""
    total_rated: int                          # BeanRatings that have a BeanTaste
    avg_axes: BeanTasteAxisAverages
    best_score: float | None
    best_bean_id: uuid.UUID | None            # resolved via bean_taste → bean_rating → bean
    top_flavor_tags: list[FlavorTagCount]      # sorted desc by count

class TasteStatsRead(SQLModel):
    """Combined sensory statistics."""
    brew_taste: BrewTasteStats
    bean_taste: BeanTasteStats
```

Two independent query groups:

- **Brew taste**: joins `brew_taste → brew` (for person_id filter and
  `brew.retired_at IS NULL`). AVG per axis, MAX(score) with `brew_taste.brew_id`
  for best reference. Flavor tags via `brew_taste_flavor_tag_link` GROUP BY.

- **Bean taste**: joins `bean_taste → bean_rating` (for person_id filter) then
  `bean_rating → bean` (for `bean.retired_at IS NULL` and to resolve
  `best_bean_id`). AVG per axis, MAX(score) with `bean_rating.bean_id` for best
  reference. Flavor tags via `bean_taste_flavor_tag_link` GROUP BY.

### GET /stats/equipment

No query params (global).

```python
class SetupUsage(SQLModel):
    """Brew setup ranked by usage."""
    id: uuid.UUID
    name: str | None
    brew_count: int

class EquipmentStatsRead(SQLModel):
    """Aggregated equipment statistics and usage rankings."""
    # Totals (non-retired, COUNT WHERE retired_at IS NULL)
    total_grinders: int
    total_brewers: int
    total_papers: int
    total_waters: int

    # Usage rankings — top 5, sorted desc by brew_count
    top_grinders: list[NamedUsageCount]
    top_brewers: list[NamedUsageCount]
    top_setups: list[SetupUsage]

    # Most-used brew method (derived through brew_setup -> brew_method)
    most_used_method: NamedUsageCount | None
```

Totals are COUNT WHERE retired_at IS NULL. Usage rankings join
`brew → brew_setup → grinder/brewer` with GROUP BY, ORDER BY count DESC,
LIMIT 5. `SetupUsage` includes `name: str | None` since brew setup names are
optional.

### GET /stats/cuppings

Query params: `person_id` (optional UUID, defaults to default person).

```python
class CuppingStatsRead(SQLModel):
    """Aggregated cupping session statistics."""
    total: int
    avg_total_score: float | None
    best_total_score: float | None
    best_cupping_id: uuid.UUID | None
    top_flavor_tags: list[FlavorTagCount]     # sorted desc by count
```

COUNT, AVG(total_score), MAX(total_score) on non-retired cuppings filtered by
person_id and retired_at IS NULL. Flavor tags via `cupping_flavor_tag_link`
M2M with GROUP BY.

## File Layout

| File | Contents |
|---|---|
| `src/beanbay/schemas/stats.py` | All response models above |
| `src/beanbay/routers/stats.py` | All 5 endpoints |
| `src/beanbay/dependencies.py` | Add `OptionalPersonIdDep` |
| `src/beanbay/main.py` | Register stats router |
| `tests/integration/test_stats.py` | Integration tests against real DB |

## Error Handling

- Explicit `person_id` that does not exist or is retired: **404**
- No data (zero brews, no beans, etc.): returns zero counts and None for
  averages/references — never errors

## Testing Strategy

Integration tests with a real SQLite database and known seed data. Each
endpoint gets its own test function asserting exact counts and averages against
the seeded state. Tests cover:

- Default person resolution (no person_id param)
- Explicit person_id filtering
- Empty state (all zeros/Nones)
- Non-existent person_id → 404
- Retired person_id → 404
