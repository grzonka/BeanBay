# Stats Endpoints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add five aggregated statistics sub-endpoints under `/api/v1/stats/` (brews, beans, taste, equipment, cuppings) to power independent dashboard widgets.

**Architecture:** Five read-only GET endpoints in a single `stats` router. Person-scoped endpoints use a shared `OptionalPersonIdDep` dependency. All queries aggregate over non-retired records using SQLModel/SQLAlchemy `func` expressions.

**Tech Stack:** FastAPI, SQLModel, SQLAlchemy `func` (COUNT, AVG, MAX), pytest with real SQLite DB.

**Spec:** `docs/superpowers/specs/2026-03-21-stats-endpoints-design.md`

---

### Task 1: Add `OptionalPersonIdDep` to dependencies

**Files:**
- Modify: `src/beanbay/dependencies.py`

- [ ] **Step 1: Write the failing test**

Create `tests/integration/test_stats_api.py` with just the person-resolution test. This test will fail because the endpoint doesn't exist yet, but it validates the dependency behavior once wired up. For now, just create the file shell:

```python
"""Integration tests for Stats endpoints."""

import uuid
from datetime import datetime, timezone

STATS_BREWS = "/api/v1/stats/brews"
STATS_BEANS = "/api/v1/stats/beans"
STATS_TASTE = "/api/v1/stats/taste"
STATS_EQUIPMENT = "/api/v1/stats/equipment"
STATS_CUPPINGS = "/api/v1/stats/cuppings"

# Reusable endpoint constants for creating seed data
PEOPLE = "/api/v1/people"
BEANS = "/api/v1/beans"
BREW_METHODS = "/api/v1/brew-methods"
BREW_SETUPS = "/api/v1/brew-setups"
BREWS = "/api/v1/brews"
GRINDERS = "/api/v1/grinders"
BREWERS = "/api/v1/brewers"
PAPERS = "/api/v1/papers"
WATERS = "/api/v1/waters"
FLAVOR_TAGS = "/api/v1/flavor-tags"
ROASTERS = "/api/v1/roasters"
ORIGINS = "/api/v1/origins"
CUPPINGS = "/api/v1/cuppings"
RATINGS = "/api/v1/beans"  # ratings are nested: /beans/{id}/ratings
BEAN_RATINGS = "/api/v1/bean-ratings"  # taste sub-resource: /bean-ratings/{id}/taste


# ======================================================================
# Helpers
# ======================================================================


def _unique(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _create_person(client, name: str | None = None) -> str:
    name = name or _unique("person")
    resp = client.post(PEOPLE, json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_bean(client, name: str | None = None, **kwargs) -> str:
    name = name or _unique("bean")
    payload = {"name": name, **kwargs}
    resp = client.post(BEANS, json=payload)
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_bag(client, bean_id: str, **kwargs) -> str:
    payload = {"weight": 250.0, **kwargs}
    resp = client.post(f"{BEANS}/{bean_id}/bags", json=payload)
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_brew_method(client, name: str | None = None) -> str:
    name = name or _unique("method")
    resp = client.post(BREW_METHODS, json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_brew_setup(
    client,
    brew_method_id: str,
    grinder_id: str | None = None,
    brewer_id: str | None = None,
    **kwargs,
) -> str:
    payload = {"brew_method_id": brew_method_id, **kwargs}
    if grinder_id:
        payload["grinder_id"] = grinder_id
    if brewer_id:
        payload["brewer_id"] = brewer_id
    resp = client.post(BREW_SETUPS, json=payload)
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_brew(
    client,
    bag_id: str,
    brew_setup_id: str,
    person_id: str,
    dose: float = 18.0,
    **kwargs,
) -> str:
    payload = {
        "bag_id": bag_id,
        "brew_setup_id": brew_setup_id,
        "person_id": person_id,
        "dose": dose,
        "brewed_at": kwargs.pop("brewed_at", _now_iso()),
        **kwargs,
    }
    resp = client.post(BREWS, json=payload)
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_grinder(client, name: str | None = None) -> str:
    name = name or _unique("grinder")
    resp = client.post(GRINDERS, json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_brewer(client, name: str | None = None) -> str:
    name = name or _unique("brewer")
    resp = client.post(BREWERS, json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_flavor_tag(client, name: str | None = None) -> str:
    name = name or _unique("tag")
    resp = client.post(FLAVOR_TAGS, json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_roaster(client, name: str | None = None) -> str:
    name = name or _unique("roaster")
    resp = client.post(ROASTERS, json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_origin(client, name: str | None = None, **kwargs) -> str:
    name = name or _unique("origin")
    resp = client.post(ORIGINS, json={"name": name, **kwargs})
    assert resp.status_code == 201
    return resp.json()["id"]
```

Create this file at `tests/integration/test_stats_api.py`.

- [ ] **Step 2: Add `OptionalPersonIdDep` to dependencies.py**

Add new imports and the dependency to `src/beanbay/dependencies.py`. The existing `SessionDep` and `validate_sort` stay unchanged. Add the following **above** `validate_sort`:

New imports to add at the top of the file (merge with existing):
```python
import uuid

from fastapi import Depends, HTTPException, Query
from sqlmodel import Session, select

from beanbay.models.person import Person
```

New code to add after `SessionDep` and before `validate_sort`:
```python
def _resolve_person_id(
    session: SessionDep,
    person_id: uuid.UUID | None = Query(default=None),
) -> uuid.UUID | None:
    """Resolve an optional person_id, falling back to the default person.

    Parameters
    ----------
    session : Session
        Database session.
    person_id : uuid.UUID | None
        Explicit person ID. If ``None``, resolves to the default person.

    Returns
    -------
    uuid.UUID | None
        Resolved person ID, or ``None`` if no default person exists.

    Raises
    ------
    HTTPException
        404 if an explicit ``person_id`` is not found or is retired.
    """
    if person_id:
        person = session.get(Person, person_id)
        if not person or person.retired_at:
            raise HTTPException(status_code=404, detail="Person not found")
        return person_id
    default = session.exec(
        select(Person).where(Person.is_default == True)  # noqa: E712
    ).first()
    return default.id if default else None


OptionalPersonIdDep = Annotated[uuid.UUID | None, Depends(_resolve_person_id)]
```

- [ ] **Step 3: Commit**

```bash
git add src/beanbay/dependencies.py tests/integration/test_stats_api.py
git commit -m "feat(stats): add OptionalPersonIdDep and test scaffold"
```

---

### Task 2: Create response schemas

**Files:**
- Create: `src/beanbay/schemas/stats.py`

- [ ] **Step 1: Create the schemas file**

Create `src/beanbay/schemas/stats.py`:

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add src/beanbay/schemas/stats.py
git commit -m "feat(stats): add response schemas for all stats endpoints"
```

---

### Task 3: Implement `GET /stats/brews` endpoint + tests

**Files:**
- Create: `src/beanbay/routers/stats.py`
- Modify: `src/beanbay/main.py` (register router)
- Modify: `tests/integration/test_stats_api.py` (add tests)

- [ ] **Step 1: Write the failing tests**

Append to `tests/integration/test_stats_api.py`:

```python
# ======================================================================
# GET /stats/brews
# ======================================================================


class TestBrewStats:
    """Tests for GET /api/v1/stats/brews."""

    def test_empty_state(self, client):
        """No brews → zero counts, None averages."""
        resp = client.get(STATS_BREWS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["this_week"] == 0
        assert data["this_month"] == 0
        assert data["total_failed"] == 0
        assert data["fail_rate"] is None
        assert data["avg_dose_g"] is None
        assert data["avg_yield_g"] is None
        assert data["avg_brew_time_s"] is None
        assert data["last_brewed_at"] is None
        assert data["by_method"] == []

    def test_with_brews(self, client):
        """Seed brews and verify counts and averages."""
        person_id = _create_person(client)
        bean_id = _create_bean(client)
        bag_id = _create_bag(client, bean_id)
        method_id = _create_brew_method(client)
        setup_id = _create_brew_setup(client, method_id)

        # Create 2 brews: one successful, one failed
        _create_brew(
            client, bag_id, setup_id, person_id,
            dose=18.0, yield_amount=36.0, total_time=30.0,
        )
        _create_brew(
            client, bag_id, setup_id, person_id,
            dose=20.0, yield_amount=40.0, total_time=25.0, is_failed=True,
        )

        resp = client.get(STATS_BREWS, params={"person_id": person_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["this_week"] == 2
        assert data["this_month"] == 2
        assert data["total_failed"] == 1
        assert data["fail_rate"] == 0.5
        assert data["avg_dose_g"] == 19.0
        assert data["avg_yield_g"] == 38.0
        assert data["avg_brew_time_s"] == 27.5
        assert data["last_brewed_at"] is not None
        assert len(data["by_method"]) == 1
        assert data["by_method"][0]["count"] == 2

    def test_person_filter(self, client):
        """Stats only count brews for the specified person."""
        person_a = _create_person(client)
        person_b = _create_person(client)
        bean_id = _create_bean(client)
        bag_id = _create_bag(client, bean_id)
        method_id = _create_brew_method(client)
        setup_id = _create_brew_setup(client, method_id)

        _create_brew(client, bag_id, setup_id, person_a, dose=18.0)
        _create_brew(client, bag_id, setup_id, person_b, dose=20.0)

        resp = client.get(STATS_BREWS, params={"person_id": person_a})
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_nonexistent_person_404(self, client):
        """Explicit unknown person_id returns 404."""
        fake_id = str(uuid.uuid4())
        resp = client.get(STATS_BREWS, params={"person_id": fake_id})
        assert resp.status_code == 404

    def test_retired_person_404(self, client):
        """Explicit retired person_id returns 404."""
        person_id = _create_person(client)
        resp = client.delete(f"{PEOPLE}/{person_id}")
        assert resp.status_code == 200

        resp = client.get(STATS_BREWS, params={"person_id": person_id})
        assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/integration/test_stats_api.py -v`
Expected: FAIL (404 on all endpoints — router not registered yet)

- [ ] **Step 3: Create the stats router with brew stats endpoint**

Create `src/beanbay/routers/stats.py`:

```python
"""Read-only stats endpoints for dashboard widgets."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from sqlalchemy import func as sa_func
from sqlmodel import select

from beanbay.dependencies import OptionalPersonIdDep, SessionDep
from beanbay.models.bean import Bag, Bean, BeanOriginLink
from beanbay.models.brew import Brew, BrewSetup, BrewTaste, BrewTasteFlavorTagLink
from beanbay.models.cupping import Cupping, CuppingFlavorTagLink
from beanbay.models.equipment import Brewer, Grinder, Paper, Water
from beanbay.models.rating import BeanRating, BeanTaste, BeanTasteFlavorTagLink
from beanbay.models.tag import BrewMethod, FlavorTag, Roaster, Origin
from beanbay.schemas.stats import (
    BeanStatsRead,
    BeanTasteAxisAverages,
    BeanTasteStats,
    BrewStatsRead,
    BrewTasteAxisAverages,
    BrewTasteStats,
    CuppingStatsRead,
    EquipmentStatsRead,
    FlavorTagCount,
    MethodBrewCount,
    NamedUsageCount,
    OriginBeanCount,
    RoasterBeanCount,
    SetupUsage,
    TasteStatsRead,
)

router = APIRouter(tags=["Stats"])


def _r(val: float | None) -> float | None:
    """Round a float to 2 decimal places, or return None."""
    return round(val, 2) if val is not None else None


def _week_start() -> datetime:
    """Return Monday 00:00 UTC of the current week."""
    now = datetime.now(timezone.utc)
    monday = now.replace(hour=0, minute=0, second=0, microsecond=0)
    monday -= timedelta(days=now.weekday())
    return monday


def _month_start() -> datetime:
    """Return 1st of current month 00:00 UTC."""
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _base_brew_filter(person_id: uuid.UUID | None):
    """Return base WHERE conditions for non-retired brews, optionally by person."""
    conditions = [Brew.retired_at.is_(None)]  # type: ignore[union-attr]
    if person_id is not None:
        conditions.append(Brew.person_id == person_id)
    return conditions


@router.get("/stats/brews", response_model=BrewStatsRead)
def get_brew_stats(
    session: SessionDep,
    person_id: OptionalPersonIdDep,
) -> BrewStatsRead:
    """Aggregated brew statistics."""
    conditions = _base_brew_filter(person_id)

    # Scalar aggregates
    row = session.exec(
        select(
            sa_func.count().label("total"),
            sa_func.sum(Brew.is_failed.cast(int)).label("total_failed"),  # type: ignore[union-attr]
            sa_func.avg(Brew.dose).label("avg_dose"),
            sa_func.avg(Brew.yield_amount).label("avg_yield"),
            sa_func.avg(Brew.total_time).label("avg_time"),
            sa_func.max(Brew.brewed_at).label("last_brewed"),
        ).where(*conditions)
    ).one()

    total = row.total or 0
    total_failed = int(row.total_failed or 0)

    # This week / this month
    week_start = _week_start()
    month_start = _month_start()

    this_week = session.exec(
        select(sa_func.count()).where(
            *conditions, Brew.brewed_at >= week_start
        )
    ).one()

    this_month = session.exec(
        select(sa_func.count()).where(
            *conditions, Brew.brewed_at >= month_start
        )
    ).one()

    # By method
    method_rows = session.exec(
        select(
            BrewMethod.id,
            BrewMethod.name,
            sa_func.count().label("cnt"),
        )
        .join(BrewSetup, BrewSetup.brew_method_id == BrewMethod.id)
        .join(Brew, Brew.brew_setup_id == BrewSetup.id)
        .where(*conditions)
        .group_by(BrewMethod.id, BrewMethod.name)
        .order_by(sa_func.count().desc())
    ).all()

    return BrewStatsRead(
        total=total,
        this_week=this_week,
        this_month=this_month,
        total_failed=total_failed,
        fail_rate=round(total_failed / total, 4) if total > 0 else None,
        avg_dose_g=round(row.avg_dose, 2) if row.avg_dose is not None else None,
        avg_yield_g=round(row.avg_yield, 2) if row.avg_yield is not None else None,
        avg_brew_time_s=round(row.avg_time, 2) if row.avg_time is not None else None,
        last_brewed_at=row.last_brewed,
        by_method=[
            MethodBrewCount(
                brew_method_id=r[0], brew_method_name=r[1], count=r[2]
            )
            for r in method_rows
        ],
    )
```

- [ ] **Step 4: Register the router in main.py**

Add to `src/beanbay/main.py` imports:
```python
from beanbay.routers.stats import router as stats_router
```

Add `stats_router` to the `_routers` list.

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/integration/test_stats_api.py::TestBrewStats -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add src/beanbay/routers/stats.py src/beanbay/main.py tests/integration/test_stats_api.py
git commit -m "feat(stats): add GET /stats/brews endpoint with tests"
```

---

### Task 4: Implement `GET /stats/beans` endpoint + tests

**Files:**
- Modify: `src/beanbay/routers/stats.py`
- Modify: `tests/integration/test_stats_api.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/integration/test_stats_api.py`:

```python
# ======================================================================
# GET /stats/beans
# ======================================================================


class TestBeanStats:
    """Tests for GET /api/v1/stats/beans."""

    def test_empty_state(self, client):
        """No beans → zero counts, empty breakdowns."""
        resp = client.get(STATS_BEANS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_beans"] == 0
        assert data["beans_active"] == 0
        assert data["total_bags"] == 0
        assert data["bags_active"] == 0
        assert data["bags_unopened"] == 0
        assert data["avg_bag_weight_g"] is None
        assert data["avg_bag_price"] is None
        assert data["mix_type_breakdown"] == {}
        assert data["use_type_breakdown"] == {}
        assert data["top_roasters"] == []
        assert data["top_origins"] == []

    def test_with_beans_and_bags(self, client):
        """Seed beans and bags, verify all counts."""
        roaster_id = _create_roaster(client)
        origin_id = _create_origin(client)

        bean_id = _create_bean(
            client,
            roaster_id=roaster_id,
            origin_ids=[origin_id],
            bean_mix_type="single_origin",
            bean_use_type="filter",
        )
        _create_bag(client, bean_id, price=15.0)
        _create_bag(client, bean_id, price=25.0, opened_at="2026-01-01")

        resp = client.get(STATS_BEANS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_beans"] == 1
        assert data["beans_active"] == 1
        assert data["total_bags"] == 2
        assert data["bags_active"] == 2
        assert data["bags_unopened"] == 1  # one has opened_at
        assert data["avg_bag_weight_g"] == 250.0
        assert data["avg_bag_price"] == 20.0
        assert data["mix_type_breakdown"]["single_origin"] == 1
        assert data["use_type_breakdown"]["filter"] == 1
        assert len(data["top_roasters"]) == 1
        assert data["top_roasters"][0]["count"] == 1
        assert len(data["top_origins"]) == 1

    def test_excludes_retired(self, client):
        """Retired beans/bags are excluded from counts."""
        bean_id = _create_bean(client)
        bag_id = _create_bag(client, bean_id)

        # Retire the bag
        resp = client.delete(f"/api/v1/bags/{bag_id}")
        assert resp.status_code == 200
        # Retire the bean
        resp = client.delete(f"/api/v1/beans/{bean_id}")
        assert resp.status_code == 200

        resp = client.get(STATS_BEANS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_beans"] == 0
        assert data["total_bags"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/integration/test_stats_api.py::TestBeanStats -v`
Expected: FAIL (endpoint not found)

- [ ] **Step 3: Add the beans endpoint to the stats router**

Add to `src/beanbay/routers/stats.py`:

```python
@router.get("/stats/beans", response_model=BeanStatsRead)
def get_bean_stats(session: SessionDep) -> BeanStatsRead:
    """Aggregated bean and bag statistics."""
    not_retired = Bean.retired_at.is_(None)  # type: ignore[union-attr]
    bag_not_retired = Bag.retired_at.is_(None)  # type: ignore[union-attr]

    # Bean counts
    total_beans = session.exec(
        select(sa_func.count()).where(not_retired).select_from(Bean)
    ).one()

    # beans_active: non-retired beans with >= 1 non-retired bag
    beans_active = session.exec(
        select(sa_func.count(sa_func.distinct(Bean.id)))
        .join(Bag, Bag.bean_id == Bean.id)
        .where(not_retired, bag_not_retired)
    ).one()

    # Mix type breakdown
    mix_rows = session.exec(
        select(Bean.bean_mix_type, sa_func.count())
        .where(not_retired)
        .group_by(Bean.bean_mix_type)
    ).all()
    mix_type_breakdown = {str(r[0].value) if r[0] else "unknown": r[1] for r in mix_rows}

    # Use type breakdown (exclude None)
    use_rows = session.exec(
        select(Bean.bean_use_type, sa_func.count())
        .where(not_retired, Bean.bean_use_type.is_not(None))  # type: ignore[union-attr]
        .group_by(Bean.bean_use_type)
    ).all()
    use_type_breakdown = {str(r[0].value): r[1] for r in use_rows}

    # Top roasters
    roaster_rows = session.exec(
        select(Roaster.id, Roaster.name, sa_func.count().label("cnt"))
        .join(Bean, Bean.roaster_id == Roaster.id)
        .where(not_retired)
        .group_by(Roaster.id, Roaster.name)
        .order_by(sa_func.count().desc())
    ).all()

    # Top origins
    origin_rows = session.exec(
        select(Origin.id, Origin.name, sa_func.count().label("cnt"))
        .join(BeanOriginLink, BeanOriginLink.origin_id == Origin.id)
        .join(Bean, Bean.id == BeanOriginLink.bean_id)
        .where(not_retired)
        .group_by(Origin.id, Origin.name)
        .order_by(sa_func.count().desc())
    ).all()

    # Bag stats
    total_bags = session.exec(
        select(sa_func.count()).where(bag_not_retired).select_from(Bag)
    ).one()
    bags_active = total_bags  # same as total non-retired

    bags_unopened = session.exec(
        select(sa_func.count()).where(
            bag_not_retired, Bag.opened_at.is_(None)  # type: ignore[union-attr]
        ).select_from(Bag)
    ).one()

    bag_agg = session.exec(
        select(
            sa_func.avg(Bag.weight).label("avg_w"),
            sa_func.avg(Bag.price).label("avg_p"),
        ).where(bag_not_retired)
    ).one()

    return BeanStatsRead(
        total_beans=total_beans,
        beans_active=beans_active,
        mix_type_breakdown=mix_type_breakdown,
        use_type_breakdown=use_type_breakdown,
        top_roasters=[
            RoasterBeanCount(roaster_id=r[0], roaster_name=r[1], count=r[2])
            for r in roaster_rows
        ],
        top_origins=[
            OriginBeanCount(origin_id=r[0], origin_name=r[1], count=r[2])
            for r in origin_rows
        ],
        total_bags=total_bags,
        bags_active=bags_active,
        bags_unopened=bags_unopened,
        avg_bag_weight_g=round(bag_agg.avg_w, 2) if bag_agg.avg_w is not None else None,
        avg_bag_price=round(bag_agg.avg_p, 2) if bag_agg.avg_p is not None else None,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/integration/test_stats_api.py::TestBeanStats -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/beanbay/routers/stats.py tests/integration/test_stats_api.py
git commit -m "feat(stats): add GET /stats/beans endpoint with tests"
```

---

### Task 5: Implement `GET /stats/taste` endpoint + tests

**Files:**
- Modify: `src/beanbay/routers/stats.py`
- Modify: `tests/integration/test_stats_api.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/integration/test_stats_api.py`:

```python
# ======================================================================
# GET /stats/taste
# ======================================================================


class TestTasteStats:
    """Tests for GET /api/v1/stats/taste."""

    def test_empty_state(self, client):
        """No tastes → zero rated, None averages."""
        resp = client.get(STATS_TASTE)
        assert resp.status_code == 200
        data = resp.json()
        bt = data["brew_taste"]
        assert bt["total_rated"] == 0
        assert bt["best_score"] is None
        assert bt["best_brew_id"] is None
        assert bt["top_flavor_tags"] == []
        for axis in ("score", "acidity", "sweetness", "body", "bitterness", "balance", "aftertaste"):
            assert bt["avg_axes"][axis] is None

        bnt = data["bean_taste"]
        assert bnt["total_rated"] == 0
        assert bnt["best_score"] is None
        assert bnt["best_bean_id"] is None

    def test_brew_taste_stats(self, client):
        """Seed brew tastes and verify averages."""
        person_id = _create_person(client)
        bean_id = _create_bean(client)
        bag_id = _create_bag(client, bean_id)
        method_id = _create_brew_method(client)
        setup_id = _create_brew_setup(client, method_id)
        tag_id = _create_flavor_tag(client, "chocolate")

        brew1_id = _create_brew(client, bag_id, setup_id, person_id, dose=18.0)
        brew2_id = _create_brew(client, bag_id, setup_id, person_id, dose=20.0)

        # Add taste to both brews (scores must be 0-10)
        client.put(
            f"{BREWS}/{brew1_id}/taste",
            json={"score": 7.0, "acidity": 6.0, "flavor_tag_ids": [tag_id]},
        )
        client.put(
            f"{BREWS}/{brew2_id}/taste",
            json={"score": 9.0, "acidity": 8.0, "flavor_tag_ids": [tag_id]},
        )

        resp = client.get(STATS_TASTE, params={"person_id": person_id})
        assert resp.status_code == 200
        bt = resp.json()["brew_taste"]
        assert bt["total_rated"] == 2
        assert bt["avg_axes"]["score"] == 8.0
        assert bt["avg_axes"]["acidity"] == 7.0
        assert bt["best_score"] == 9.0
        assert bt["best_brew_id"] == brew2_id
        assert len(bt["top_flavor_tags"]) == 1
        assert bt["top_flavor_tags"][0]["count"] == 2

    def test_bean_taste_stats(self, client):
        """Seed bean tastes and verify averages."""
        person_id = _create_person(client)
        bean_id = _create_bean(client)

        # Create two ratings with tastes (scores 0-10, use PUT on /bean-ratings/{id}/taste)
        r1 = client.post(
            f"{BEANS}/{bean_id}/ratings",
            json={"person_id": person_id},
        )
        assert r1.status_code == 201
        rating1_id = r1.json()["id"]
        resp = client.put(
            f"{BEAN_RATINGS}/{rating1_id}/taste",
            json={"score": 7.0, "complexity": 6.0},
        )
        assert resp.status_code in (200, 201)

        r2 = client.post(
            f"{BEANS}/{bean_id}/ratings",
            json={"person_id": person_id},
        )
        assert r2.status_code == 201
        rating2_id = r2.json()["id"]
        resp = client.put(
            f"{BEAN_RATINGS}/{rating2_id}/taste",
            json={"score": 9.0, "complexity": 8.0},
        )
        assert resp.status_code in (200, 201)

        resp = client.get(STATS_TASTE, params={"person_id": person_id})
        assert resp.status_code == 200
        bnt = resp.json()["bean_taste"]
        assert bnt["total_rated"] == 2
        assert bnt["avg_axes"]["score"] == 8.0
        assert bnt["avg_axes"]["complexity"] == 7.0
        assert bnt["best_score"] == 9.0
        assert bnt["best_bean_id"] == bean_id
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/integration/test_stats_api.py::TestTasteStats -v`
Expected: FAIL

- [ ] **Step 3: Add the taste endpoint to the stats router**

Add a helper for flavor tag frequency and the taste endpoint to `src/beanbay/routers/stats.py`:

```python
def _flavor_tag_counts(session, link_model, entity_conditions):
    """Query top flavor tags through a M2M link table.

    Parameters
    ----------
    session : Session
        DB session.
    link_model : type
        The M2M link model (e.g. BrewTasteFlavorTagLink).
    entity_conditions : list
        WHERE conditions that have already been applied to the parent entity.
        This function joins FlavorTag to the link table only — the caller
        must ensure the link table IDs are already filtered.

    Returns
    -------
    list[FlavorTagCount]
    """
    rows = session.exec(
        select(
            FlavorTag.id,
            FlavorTag.name,
            sa_func.count().label("cnt"),
        )
        .join(link_model, link_model.flavor_tag_id == FlavorTag.id)
        .where(*entity_conditions)
        .group_by(FlavorTag.id, FlavorTag.name)
        .order_by(sa_func.count().desc())
    ).all()
    return [
        FlavorTagCount(flavor_tag_id=r[0], flavor_tag_name=r[1], count=r[2])
        for r in rows
    ]


@router.get("/stats/taste", response_model=TasteStatsRead)
def get_taste_stats(
    session: SessionDep,
    person_id: OptionalPersonIdDep,
) -> TasteStatsRead:
    """Aggregated sensory statistics."""
    # --- Brew Taste ---
    brew_conditions = [Brew.retired_at.is_(None)]  # type: ignore[union-attr]
    if person_id is not None:
        brew_conditions.append(Brew.person_id == person_id)

    bt_agg = session.exec(
        select(
            sa_func.count().label("total"),
            sa_func.avg(BrewTaste.score),
            sa_func.avg(BrewTaste.acidity),
            sa_func.avg(BrewTaste.sweetness),
            sa_func.avg(BrewTaste.body),
            sa_func.avg(BrewTaste.bitterness),
            sa_func.avg(BrewTaste.balance),
            sa_func.avg(BrewTaste.aftertaste),
        )
        .join(Brew, Brew.id == BrewTaste.brew_id)
        .where(*brew_conditions)
    ).one()

    # Best brew taste score
    best_bt = session.exec(
        select(BrewTaste.score, BrewTaste.brew_id)
        .join(Brew, Brew.id == BrewTaste.brew_id)
        .where(*brew_conditions, BrewTaste.score.is_not(None))  # type: ignore[union-attr]
        .order_by(BrewTaste.score.desc())  # type: ignore[union-attr]
        .limit(1)
    ).first()

    # Brew taste flavor tags — filter link table through brew_taste IDs of non-retired brews
    bt_link_conditions = [
        BrewTasteFlavorTagLink.brew_taste_id.in_(  # type: ignore[union-attr]
            select(BrewTaste.id)
            .join(Brew, Brew.id == BrewTaste.brew_id)
            .where(*brew_conditions)
        )
    ]
    bt_tags = _flavor_tag_counts(session, BrewTasteFlavorTagLink, bt_link_conditions)

    brew_taste = BrewTasteStats(
        total_rated=bt_agg[0] or 0,
        avg_axes=BrewTasteAxisAverages(
            score=_r(bt_agg[1]),
            acidity=_r(bt_agg[2]),
            sweetness=_r(bt_agg[3]),
            body=_r(bt_agg[4]),
            bitterness=_r(bt_agg[5]),
            balance=_r(bt_agg[6]),
            aftertaste=_r(bt_agg[7]),
        ),
        best_score=best_bt[0] if best_bt else None,
        best_brew_id=best_bt[1] if best_bt else None,
        top_flavor_tags=bt_tags,
    )

    # --- Bean Taste ---
    bean_conditions = [Bean.retired_at.is_(None)]  # type: ignore[union-attr]
    rating_conditions = [BeanRating.retired_at.is_(None)]  # type: ignore[union-attr]
    if person_id is not None:
        rating_conditions.append(BeanRating.person_id == person_id)

    bnt_agg = session.exec(
        select(
            sa_func.count().label("total"),
            sa_func.avg(BeanTaste.score),
            sa_func.avg(BeanTaste.acidity),
            sa_func.avg(BeanTaste.sweetness),
            sa_func.avg(BeanTaste.body),
            sa_func.avg(BeanTaste.complexity),
            sa_func.avg(BeanTaste.aroma),
            sa_func.avg(BeanTaste.clean_cup),
        )
        .join(BeanRating, BeanRating.id == BeanTaste.bean_rating_id)
        .join(Bean, Bean.id == BeanRating.bean_id)
        .where(*bean_conditions, *rating_conditions)
    ).one()

    # Best bean taste score → resolve bean_id through bean_rating
    best_bnt = session.exec(
        select(BeanTaste.score, BeanRating.bean_id)
        .join(BeanRating, BeanRating.id == BeanTaste.bean_rating_id)
        .join(Bean, Bean.id == BeanRating.bean_id)
        .where(*bean_conditions, *rating_conditions, BeanTaste.score.is_not(None))  # type: ignore[union-attr]
        .order_by(BeanTaste.score.desc())  # type: ignore[union-attr]
        .limit(1)
    ).first()

    # Bean taste flavor tags
    bnt_link_conditions = [
        BeanTasteFlavorTagLink.bean_taste_id.in_(  # type: ignore[union-attr]
            select(BeanTaste.id)
            .join(BeanRating, BeanRating.id == BeanTaste.bean_rating_id)
            .join(Bean, Bean.id == BeanRating.bean_id)
            .where(*bean_conditions, *rating_conditions)
        )
    ]
    bnt_tags = _flavor_tag_counts(session, BeanTasteFlavorTagLink, bnt_link_conditions)

    bean_taste = BeanTasteStats(
        total_rated=bnt_agg[0] or 0,
        avg_axes=BeanTasteAxisAverages(
            score=_r(bnt_agg[1]),
            acidity=_r(bnt_agg[2]),
            sweetness=_r(bnt_agg[3]),
            body=_r(bnt_agg[4]),
            complexity=_r(bnt_agg[5]),
            aroma=_r(bnt_agg[6]),
            clean_cup=_r(bnt_agg[7]),
        ),
        best_score=best_bnt[0] if best_bnt else None,
        best_bean_id=best_bnt[1] if best_bnt else None,
        top_flavor_tags=bnt_tags,
    )

    return TasteStatsRead(brew_taste=brew_taste, bean_taste=bean_taste)
```

Note: `_r()` helper was already added in Task 3 when the router file was created.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/integration/test_stats_api.py::TestTasteStats -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/beanbay/routers/stats.py tests/integration/test_stats_api.py
git commit -m "feat(stats): add GET /stats/taste endpoint with tests"
```

---

### Task 6: Implement `GET /stats/equipment` endpoint + tests

**Files:**
- Modify: `src/beanbay/routers/stats.py`
- Modify: `tests/integration/test_stats_api.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/integration/test_stats_api.py`:

```python
# ======================================================================
# GET /stats/equipment
# ======================================================================


class TestEquipmentStats:
    """Tests for GET /api/v1/stats/equipment."""

    def test_empty_state(self, client):
        """No equipment → zero totals, empty rankings."""
        resp = client.get(STATS_EQUIPMENT)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_grinders"] == 0
        assert data["total_brewers"] == 0
        assert data["total_papers"] == 0
        assert data["total_waters"] == 0
        assert data["top_grinders"] == []
        assert data["top_brewers"] == []
        assert data["top_setups"] == []
        assert data["most_used_method"] is None

    def test_equipment_counts_and_rankings(self, client):
        """Seed equipment + brews and verify totals and rankings."""
        person_id = _create_person(client)
        bean_id = _create_bean(client)
        bag_id = _create_bag(client, bean_id)
        method_id = _create_brew_method(client)
        grinder_id = _create_grinder(client)
        brewer_id = _create_brewer(client)

        setup_id = _create_brew_setup(
            client, method_id, grinder_id=grinder_id, brewer_id=brewer_id
        )

        # Create 3 brews using this setup
        for _ in range(3):
            _create_brew(client, bag_id, setup_id, person_id)

        resp = client.get(STATS_EQUIPMENT)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_grinders"] == 1
        assert data["total_brewers"] == 1
        assert len(data["top_grinders"]) == 1
        assert data["top_grinders"][0]["brew_count"] == 3
        assert len(data["top_brewers"]) == 1
        assert data["top_brewers"][0]["brew_count"] == 3
        assert len(data["top_setups"]) == 1
        assert data["top_setups"][0]["brew_count"] == 3
        assert data["most_used_method"] is not None
        assert data["most_used_method"]["brew_count"] == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/integration/test_stats_api.py::TestEquipmentStats -v`
Expected: FAIL

- [ ] **Step 3: Add the equipment endpoint to the stats router**

Add to `src/beanbay/routers/stats.py`:

```python
@router.get("/stats/equipment", response_model=EquipmentStatsRead)
def get_equipment_stats(session: SessionDep) -> EquipmentStatsRead:
    """Aggregated equipment statistics and usage rankings."""
    brew_active = Brew.retired_at.is_(None)  # type: ignore[union-attr]

    # Totals (non-retired)
    total_grinders = session.exec(
        select(sa_func.count()).where(Grinder.retired_at.is_(None)).select_from(Grinder)  # type: ignore[union-attr]
    ).one()
    total_brewers = session.exec(
        select(sa_func.count()).where(Brewer.retired_at.is_(None)).select_from(Brewer)  # type: ignore[union-attr]
    ).one()
    total_papers = session.exec(
        select(sa_func.count()).where(Paper.retired_at.is_(None)).select_from(Paper)  # type: ignore[union-attr]
    ).one()
    total_waters = session.exec(
        select(sa_func.count()).where(Water.retired_at.is_(None)).select_from(Water)  # type: ignore[union-attr]
    ).one()

    # Top grinders by brew count
    grinder_rows = session.exec(
        select(Grinder.id, Grinder.name, sa_func.count().label("cnt"))
        .join(BrewSetup, BrewSetup.grinder_id == Grinder.id)
        .join(Brew, Brew.brew_setup_id == BrewSetup.id)
        .where(brew_active)
        .group_by(Grinder.id, Grinder.name)
        .order_by(sa_func.count().desc())
        .limit(5)
    ).all()

    # Top brewers by brew count
    brewer_rows = session.exec(
        select(Brewer.id, Brewer.name, sa_func.count().label("cnt"))
        .join(BrewSetup, BrewSetup.brewer_id == Brewer.id)
        .join(Brew, Brew.brew_setup_id == BrewSetup.id)
        .where(brew_active)
        .group_by(Brewer.id, Brewer.name)
        .order_by(sa_func.count().desc())
        .limit(5)
    ).all()

    # Top setups by brew count
    setup_rows = session.exec(
        select(BrewSetup.id, BrewSetup.name, sa_func.count().label("cnt"))
        .join(Brew, Brew.brew_setup_id == BrewSetup.id)
        .where(brew_active)
        .group_by(BrewSetup.id, BrewSetup.name)
        .order_by(sa_func.count().desc())
        .limit(5)
    ).all()

    # Most-used brew method
    method_row = session.exec(
        select(BrewMethod.id, BrewMethod.name, sa_func.count().label("cnt"))
        .join(BrewSetup, BrewSetup.brew_method_id == BrewMethod.id)
        .join(Brew, Brew.brew_setup_id == BrewSetup.id)
        .where(brew_active)
        .group_by(BrewMethod.id, BrewMethod.name)
        .order_by(sa_func.count().desc())
        .limit(1)
    ).first()

    return EquipmentStatsRead(
        total_grinders=total_grinders,
        total_brewers=total_brewers,
        total_papers=total_papers,
        total_waters=total_waters,
        top_grinders=[
            NamedUsageCount(id=r[0], name=r[1], brew_count=r[2])
            for r in grinder_rows
        ],
        top_brewers=[
            NamedUsageCount(id=r[0], name=r[1], brew_count=r[2])
            for r in brewer_rows
        ],
        top_setups=[
            SetupUsage(id=r[0], name=r[1], brew_count=r[2])
            for r in setup_rows
        ],
        most_used_method=NamedUsageCount(
            id=method_row[0], name=method_row[1], brew_count=method_row[2]
        ) if method_row else None,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/integration/test_stats_api.py::TestEquipmentStats -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/beanbay/routers/stats.py tests/integration/test_stats_api.py
git commit -m "feat(stats): add GET /stats/equipment endpoint with tests"
```

---

### Task 7: Implement `GET /stats/cuppings` endpoint + tests

**Files:**
- Modify: `src/beanbay/routers/stats.py`
- Modify: `tests/integration/test_stats_api.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/integration/test_stats_api.py`:

```python
# ======================================================================
# GET /stats/cuppings
# ======================================================================


class TestCuppingStats:
    """Tests for GET /api/v1/stats/cuppings."""

    def test_empty_state(self, client):
        """No cuppings → zero counts, None scores."""
        resp = client.get(STATS_CUPPINGS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["avg_total_score"] is None
        assert data["best_total_score"] is None
        assert data["best_cupping_id"] is None
        assert data["top_flavor_tags"] == []

    def test_with_cuppings(self, client):
        """Seed cuppings and verify scores."""
        person_id = _create_person(client)
        bean_id = _create_bean(client)
        bag_id = _create_bag(client, bean_id)
        tag_id = _create_flavor_tag(client)

        c1 = client.post(CUPPINGS, json={
            "bag_id": bag_id,
            "person_id": person_id,
            "cupped_at": _now_iso(),
            "total_score": 80.0,
            "flavor_tag_ids": [tag_id],
        })
        assert c1.status_code == 201

        c2 = client.post(CUPPINGS, json={
            "bag_id": bag_id,
            "person_id": person_id,
            "cupped_at": _now_iso(),
            "total_score": 90.0,
            "flavor_tag_ids": [tag_id],
        })
        assert c2.status_code == 201
        c2_id = c2.json()["id"]

        resp = client.get(STATS_CUPPINGS, params={"person_id": person_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["avg_total_score"] == 85.0
        assert data["best_total_score"] == 90.0
        assert data["best_cupping_id"] == c2_id
        assert len(data["top_flavor_tags"]) == 1
        assert data["top_flavor_tags"][0]["count"] == 2

    def test_person_filter(self, client):
        """Cuppings only count for the specified person."""
        person_a = _create_person(client)
        person_b = _create_person(client)
        bean_id = _create_bean(client)
        bag_id = _create_bag(client, bean_id)

        client.post(CUPPINGS, json={
            "bag_id": bag_id, "person_id": person_a,
            "cupped_at": _now_iso(), "total_score": 80.0,
        })
        client.post(CUPPINGS, json={
            "bag_id": bag_id, "person_id": person_b,
            "cupped_at": _now_iso(), "total_score": 90.0,
        })

        resp = client.get(STATS_CUPPINGS, params={"person_id": person_a})
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        assert resp.json()["avg_total_score"] == 80.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/integration/test_stats_api.py::TestCuppingStats -v`
Expected: FAIL

- [ ] **Step 3: Add the cuppings endpoint to the stats router**

Add to `src/beanbay/routers/stats.py`:

```python
@router.get("/stats/cuppings", response_model=CuppingStatsRead)
def get_cupping_stats(
    session: SessionDep,
    person_id: OptionalPersonIdDep,
) -> CuppingStatsRead:
    """Aggregated cupping session statistics."""
    conditions = [Cupping.retired_at.is_(None)]  # type: ignore[union-attr]
    if person_id is not None:
        conditions.append(Cupping.person_id == person_id)

    agg = session.exec(
        select(
            sa_func.count().label("total"),
            sa_func.avg(Cupping.total_score).label("avg_score"),
        ).where(*conditions)
    ).one()

    total = agg[0] or 0

    # Best cupping
    best = session.exec(
        select(Cupping.total_score, Cupping.id)
        .where(*conditions, Cupping.total_score.is_not(None))  # type: ignore[union-attr]
        .order_by(Cupping.total_score.desc())  # type: ignore[union-attr]
        .limit(1)
    ).first()

    # Flavor tags
    tag_conditions = [
        CuppingFlavorTagLink.cupping_id.in_(  # type: ignore[union-attr]
            select(Cupping.id).where(*conditions)
        )
    ]
    tags = _flavor_tag_counts(session, CuppingFlavorTagLink, tag_conditions)

    return CuppingStatsRead(
        total=total,
        avg_total_score=_r(agg[1]),
        best_total_score=best[0] if best else None,
        best_cupping_id=best[1] if best else None,
        top_flavor_tags=tags,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/integration/test_stats_api.py::TestCuppingStats -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/beanbay/routers/stats.py tests/integration/test_stats_api.py
git commit -m "feat(stats): add GET /stats/cuppings endpoint with tests"
```

---

### Task 8: Run full test suite and verify

**Files:**
- None (verification only)

- [ ] **Step 1: Run the full stats test suite**

Run: `uv run pytest tests/integration/test_stats_api.py -v`
Expected: all tests PASS

- [ ] **Step 2: Run the complete project test suite**

Run: `uv run pytest tests/ -v`
Expected: all existing + new tests PASS (no regressions)

- [ ] **Step 3: Run pre-commit checks**

Run: `uvx prek --all-files`
Expected: all checks pass

- [ ] **Step 4: Fix any linting issues and commit if needed**

If pre-commit found issues, fix them and commit:
```bash
git add -u
git commit -m "style: fix linting issues in stats endpoints"
```
