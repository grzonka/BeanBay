# BeanBay REST API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the complete BeanBay REST API per the approved design spec at `docs/superpowers/specs/2026-03-21-beanbay-api-design.md`.

**Architecture:** FastAPI + SQLModel with a flat module layout (`config`, `database`, `models/`, `schemas/`, `routers/`, `utils/`). SQLite default with WAL mode, configurable via `BEANBAY_DATABASE_URL`. Alembic for migrations, pint for unit conversion, FastAPI DI for sessions, lifespan for startup seeding. Cherry-pick grinder display and brewer capability logic from the `main` branch.

**Tech Stack:** Python 3.11+, FastAPI, SQLModel, Pydantic Settings, Alembic, Pint, SQLite, pytest + httpx (no mocks)

**Spec:** `docs/superpowers/specs/2026-03-21-beanbay-api-design.md`

**Important conventions:**
- Use `uv` for all package management (`uv sync`, `uv add`, `uv run python`)
- Use `uvx prek --all-files` for pre-commit (not `uvx pre-commit`)
- Docstrings follow numpy style
- Never modify tests marked `@pytest.mark.protected`
- Use Context7 for FastAPI/SQLModel docs when writing implementation code

---

## File Structure

```
src/beanbay/
├── __init__.py                  # existing (empty)
├── _version.py                  # existing (setuptools_scm)
├── main.py                      # FastAPI app + lifespan
├── config.py                    # pydantic-settings (BEANBAY_ prefix)
├── database.py                  # engine, get_session DI
├── models/
│   ├── __init__.py              # re-export all models for Alembic
│   ├── base.py                  # UUIDModel base, TimestampMixin
│   ├── tag.py                   # FlavorTag, Origin, Roaster, ProcessMethod, BeanVariety, BrewMethod, StopMode
│   ├── person.py                # Person
│   ├── bean.py                  # Bean, Bag + junction tables
│   ├── equipment.py             # Grinder, Brewer, Paper, Water, WaterMineral + junctions
│   ├── brew.py                  # BrewSetup, Brew, BrewTaste + junction
│   └── rating.py                # BeanRating, BeanTaste + junction
├── schemas/
│   ├── __init__.py
│   ├── common.py                # PaginatedResponse[T], pagination/sort query params
│   ├── tag.py                   # Lookup table schemas (all 7)
│   ├── person.py                # Person schemas
│   ├── bean.py                  # Bean/Bag schemas
│   ├── equipment.py             # Grinder/Brewer/Paper/Water schemas
│   ├── brew.py                  # BrewSetup/Brew/BrewTaste schemas
│   └── rating.py                # BeanRating/BeanTaste schemas
├── routers/
│   ├── __init__.py
│   ├── lookup.py                # 7 lookup resource CRUD routers
│   ├── people.py                # /people
│   ├── beans.py                 # /beans + /beans/{id}/bags + /bags
│   ├── equipment.py             # /grinders, /brewers, /papers, /waters
│   ├── brew_setups.py           # /brew-setups
│   ├── brews.py                 # /brews + /brews/{id}/taste
│   └── ratings.py               # /beans/{id}/ratings + /bean-ratings
├── utils/
│   ├── grinder_display.py       # cherry-picked to_display/from_display
│   ├── brewer_capabilities.py   # cherry-picked derive_tier()
│   └── units.py                 # pint unit conversion helpers
└── seed.py                      # brew methods, stop modes, default person
migrations/
├── env.py                       # Alembic env targeting SQLModel.metadata
├── script.py.mako               # migration template
└── versions/                    # auto-generated migrations
tests/
├── conftest.py                  # shared: engine, session, client fixtures
├── unit/
│   ├── conftest.py
│   ├── test_grinder_display.py
│   ├── test_brewer_tier.py
│   ├── test_unit_conversion.py
│   └── test_models.py
└── integration/
    ├── conftest.py
    ├── test_lookup_api.py
    ├── test_people_api.py
    ├── test_beans_api.py
    ├── test_equipment_api.py
    ├── test_brew_setups_api.py
    ├── test_brews_api.py
    ├── test_ratings_api.py
    └── test_pagination.py
```

---

**Note on task granularity:** Tasks 2, 5, and 8 are larger than the others due to
the number of models/schemas/routers they cover. When executing, the implementer
should commit at natural intermediate points within these tasks (e.g., after models,
after schemas, after router) rather than waiting until the end.

---

## Task 1: Project Foundation — Config, Database, Base Models

**Files:**
- Create: `src/beanbay/config.py`
- Create: `src/beanbay/database.py`
- Create: `src/beanbay/models/__init__.py`
- Create: `src/beanbay/models/base.py`
- Create: `src/beanbay/main.py`
- Modify: `pyproject.toml` (add `pint` dependency)
- Create: `tests/conftest.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/unit/conftest.py`
- Create: `tests/integration/__init__.py`
- Create: `tests/integration/conftest.py`
- Test: `tests/unit/test_models.py`

- [ ] **Step 1: Add `pint` dependency**

```bash
uv add pint>=0.24
```

- [ ] **Step 2: Create `src/beanbay/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///beanbay.db"
    default_person_name: str = "Default"

    model_config = SettingsConfigDict(env_prefix="BEANBAY_")


settings = Settings()
```

- [ ] **Step 3: Create `src/beanbay/database.py`**

Use Context7 on SQLModel for the engine + DI pattern. Key points:
- `check_same_thread=False` for SQLite only
- WAL mode via event listener for SQLite only
- `get_session()` as a generator for `Depends()`

```python
from collections.abc import Generator

from sqlalchemy import event
from sqlmodel import Session, create_engine

from beanbay.config import settings

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(settings.database_url, connect_args=connect_args)

if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _set_sqlite_wal(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
```

- [ ] **Step 4: Create `src/beanbay/models/base.py`**

Shared base for all models — no mixin needed, just document the patterns.
Use `sa_column_kwargs` for server-side timestamps.

```python
import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def uuid4_default() -> uuid.UUID:
    return uuid.uuid4()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
```

(Models will use these helpers directly rather than a mixin class — keeps SQLModel
inheritance simple and avoids metaclass issues.)

Note: all updatable entities (Bean, Bag, Brew, BrewSetup, BrewTaste, BeanTaste,
Brewer, Grinder, Paper, Water, Person) MUST include `updated_at` with
`sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()}`.

- [ ] **Step 5: Create `src/beanbay/models/__init__.py`**

Empty for now — will re-export models as they're created:

```python
# Re-export all models so Alembic can discover them via SQLModel.metadata
```

- [ ] **Step 6: Create `src/beanbay/main.py`** (minimal — just the app)

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: Alembic migrations, seeding
    yield


app = FastAPI(title="BeanBay", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 7: Create test fixtures**

`tests/conftest.py` — uses nested transactions (SAVEPOINT) for isolation. Each
test runs inside a savepoint that is rolled back after the test, ensuring no
data leaks between tests even when routers commit:

```python
import pytest
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from beanbay.database import get_session
from beanbay.main import app


@pytest.fixture(name="engine", scope="session")
def engine_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine):
    """Provide a transactional session that rolls back after each test.

    Uses nested transactions (SAVEPOINT) so that commits inside routers
    do not persist data between tests.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    # Begin a nested transaction (SAVEPOINT)
    nested = connection.begin_nested()

    # If the application code calls session.commit(), restart the savepoint
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(name="client")
def client_fixture(session):
    from fastapi.testclient import TestClient

    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
```

`tests/unit/__init__.py`: empty
`tests/unit/conftest.py`: empty (placeholder)
`tests/integration/__init__.py`: empty
`tests/integration/conftest.py`: empty (placeholder)

- [ ] **Step 8: Write smoke test**

`tests/integration/test_health.py`:
```python
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 9: Run tests**

```bash
uv run pytest tests/integration/test_health.py -v
```

Expected: PASS

- [ ] **Step 10: Commit**

```bash
git add src/beanbay/config.py src/beanbay/database.py src/beanbay/models/ src/beanbay/main.py tests/ pyproject.toml uv.lock
git commit -m "feat: project foundation — config, database, base models, test fixtures"
```

---

## Task 2: Lookup Table Models + Schemas + Router

**Files:**
- Create: `src/beanbay/models/tag.py`
- Create: `src/beanbay/schemas/__init__.py`
- Create: `src/beanbay/schemas/common.py`
- Create: `src/beanbay/schemas/tag.py`
- Create: `src/beanbay/routers/__init__.py`
- Create: `src/beanbay/routers/lookup.py`
- Modify: `src/beanbay/models/__init__.py`
- Modify: `src/beanbay/main.py`
- Test: `tests/integration/test_lookup_api.py`

- [ ] **Step 1: Create lookup models** in `src/beanbay/models/tag.py`

7 lookup tables, all identical shape: `id` (UUID PK), `name` (str, unique), `created_at`.
Use a single pattern. Models: `FlavorTag`, `Origin`, `Roaster`, `ProcessMethod`, `BeanVariety`, `BrewMethod`, `StopMode`.

Each model follows:
```python
import uuid
from datetime import datetime

from sqlalchemy import func
from sqlmodel import Field, SQLModel

from beanbay.models.base import uuid4_default


class FlavorTag(SQLModel, table=True):
    __tablename__ = "flavor_tags"

    id: uuid.UUID = Field(default_factory=uuid4_default, primary_key=True)
    name: str = Field(unique=True, index=True)
    created_at: datetime = Field(
        sa_column_kwargs={"server_default": func.now()}
    )
    retired_at: datetime | None = None
```

Repeat for all 7 models with appropriate `__tablename__`.
Lookup tables have `created_at` + `retired_at` but NOT `updated_at` (per spec).

- [ ] **Step 2: Create `src/beanbay/schemas/common.py`**

```python
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
```

- [ ] **Step 3: Create `src/beanbay/schemas/tag.py`**

For each lookup table, create Base/Create/Update/Read schemas. Example pattern:

```python
import uuid
from datetime import datetime

from sqlmodel import SQLModel


class FlavorTagBase(SQLModel):
    name: str


class FlavorTagCreate(FlavorTagBase):
    pass


class FlavorTagUpdate(SQLModel):
    name: str | None = None


class FlavorTagRead(FlavorTagBase):
    id: uuid.UUID
    created_at: datetime
```

Repeat for all 7 lookup types.

- [ ] **Step 4: Create `src/beanbay/routers/lookup.py`**

Generic CRUD router factory for lookup tables. Since all 7 are identical shape,
create a factory function that generates a router for a given model+schemas:

```python
from enum import Enum
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, col, select

from beanbay.database import get_session
from beanbay.schemas.common import PaginatedResponse


def create_lookup_router(
    *,
    model_class,
    create_schema,
    update_schema,
    read_schema,
    prefix: str,
    tag: str,
    sortable_fields: list[str] | None = None,
) -> APIRouter:
    router = APIRouter(prefix=f"/{prefix}", tags=[tag])
    allowed_sort = sortable_fields or ["name", "created_at"]

    @router.get("", response_model=PaginatedResponse[read_schema])
    def list_items(
        q: str | None = None,
        include_retired: bool = False,
        limit: int = Query(default=50, le=200),
        offset: int = 0,
        sort_by: str = "name",
        sort_dir: str = "asc",
        session: Session = Depends(get_session),
    ):
        if sort_by not in allowed_sort:
            raise HTTPException(422, f"sort_by must be one of: {allowed_sort}")
        if sort_dir not in ("asc", "desc"):
            raise HTTPException(422, "sort_dir must be 'asc' or 'desc'")

        query = select(model_class)
        if not include_retired:
            query = query.where(model_class.retired_at == None)  # noqa: E711
        if q:
            query = query.where(col(model_class.name).icontains(q))

        # Sorting
        sort_col = getattr(model_class, sort_by)
        query = query.order_by(sort_col.desc() if sort_dir == "desc" else sort_col)

        total_query = select(func.count()).select_from(query.subquery())
        total = session.exec(total_query).one()
        items = session.exec(query.offset(offset).limit(limit)).all()
        return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)

    # ... POST (201), GET/{id}, PATCH/{id}, DELETE/{id} (soft-delete via retired_at)

    return router
```

The factory also accepts an optional `dependent_models` parameter — a list of
`(model_class, fk_field)` tuples. On DELETE, the factory checks if any active
(non-retired) rows in the dependent models reference the item. If so, it returns
409 Conflict instead of soft-deleting. This builds referential integrity in from
the start rather than retrofitting it in Task 14.

```python
    # In the DELETE endpoint of the factory:
    if dependent_models:
        for dep_model, fk_field in dependent_models:
            ref_query = select(func.count()).where(
                getattr(dep_model, fk_field) == item_id,
                dep_model.retired_at == None,  # noqa: E711
            )
            if session.exec(ref_query).one() > 0:
                raise HTTPException(
                    409, f"Cannot retire: referenced by active {dep_model.__tablename__}"
                )
```

Create 7 routers using this factory. Initially pass `dependent_models=None` for
all. In Task 14, fill in the actual dependencies (e.g., Origin depends on Bean
via bean_origins).

- [ ] **Step 5: Wire routers into `main.py`**

```python
from beanbay.routers.lookup import flavor_tags_router, origins_router, ...

app.include_router(flavor_tags_router, prefix="/api/v1")
# ... repeat for all lookup routers
```

- [ ] **Step 6: Update `src/beanbay/models/__init__.py`** to import all tag models.

- [ ] **Step 7: Write integration tests** in `tests/integration/test_lookup_api.py`

Test one lookup resource thoroughly (FlavorTag), then smoke-test the others:
- POST creates and returns 201
- GET list returns paginated results
- GET list with `?q=` filters correctly
- GET by ID returns the item
- PATCH updates the name
- DELETE soft-deletes (sets retired_at)
- GET list excludes retired by default, includes with `?include_retired=true`
- POST with duplicate name returns 409/422

- [ ] **Step 8: Run tests**

```bash
uv run pytest tests/integration/test_lookup_api.py -v
```

- [ ] **Step 9: Commit**

```bash
git commit -m "feat: lookup table models, schemas, and generic CRUD router"
```

---

## Task 3: Person Model + Router

**Files:**
- Create: `src/beanbay/models/person.py`
- Create: `src/beanbay/schemas/person.py`
- Create: `src/beanbay/routers/people.py`
- Modify: `src/beanbay/models/__init__.py`
- Modify: `src/beanbay/main.py`
- Test: `tests/integration/test_people_api.py`

- [ ] **Step 1: Create Person model** with `is_default` logic

Key: only one person can have `is_default=True`. The PATCH endpoint handles this
by unsetting the previous default when a new default is set.

- [ ] **Step 2: Create Person schemas** (Base/Create/Update/Read)

PersonRead includes computed `is_retired: bool` from `retired_at`.

- [ ] **Step 3: Create `/people` router** with CRUD + default person logic

PATCH with `is_default: true` must unset the previous default person in the same transaction.

- [ ] **Step 4: Write integration tests**

- POST creates person
- PATCH sets default (verify previous default is unset)
- Soft-delete works
- Cannot delete default person (or can — decide based on spec: spec allows it)

- [ ] **Step 5: Run tests, commit**

```bash
uv run pytest tests/integration/test_people_api.py -v
git commit -m "feat: person model with default person support"
```

---

## Task 4: Cherry-Pick Utils from Main Branch

**Files:**
- Create: `src/beanbay/utils/grinder_display.py`
- Create: `src/beanbay/utils/brewer_capabilities.py`
- Create: `src/beanbay/utils/__init__.py`
- Test: `tests/unit/test_grinder_display.py`
- Test: `tests/unit/test_brewer_tier.py`

- [ ] **Step 1: Extract grinder display logic from main**

```bash
git show main:app/models/equipment.py > /tmp/old_equipment.py
```

Extract `to_display()` and `from_display()` as standalone functions that accept
ring config (list of `[min, max, step]` tuples) instead of accessing `self`.
Also extract `linear_bounds()` and helper `_ring_position_counts()`.

- [ ] **Step 2: Write unit tests for grinder display**

Test cases from main's grinder models:
- Single ring decimal (Niche Zero): `to_display(15.5, [(0, 50, 0.5)])` → `"15.5"`
- Multi-ring 1Zpresso: `to_display(101, [(0, 4, 1), (0, 9, 1), (0, 3, 1)])` → `"2.5.1"`
- Round-trip: `from_display(to_display(x)) == x` for various values
- Edge cases: min value, max value, zero

- [ ] **Step 3: Extract brewer capabilities from main**

```bash
git show main:app/utils/brewer_capabilities.py > /tmp/old_brewer_caps.py
```

`derive_tier()` is nearly verbatim — takes any object with `flow_control_type`,
`pressure_control_type`, `preinfusion_type`, `temp_control_type` attributes.

- [ ] **Step 4: Write unit tests for brewer tier**

Test each tier level with appropriate attribute combinations.
Use simple `SimpleNamespace` or dataclass objects, not mocks.

- [ ] **Step 5: Run tests, commit**

```bash
uv run pytest tests/unit/test_grinder_display.py tests/unit/test_brewer_tier.py -v
git commit -m "feat: cherry-pick grinder display and brewer tier utilities

Adapted from main branch (original author: grzonka).
Refactored from ORM methods to standalone functions."
```

---

## Task 5: Equipment Models + Schemas + Router

**Files:**
- Create: `src/beanbay/models/equipment.py`
- Create: `src/beanbay/schemas/equipment.py`
- Create: `src/beanbay/routers/equipment.py`
- Modify: `src/beanbay/models/__init__.py`
- Modify: `src/beanbay/main.py`
- Test: `tests/integration/test_equipment_api.py`

- [ ] **Step 1: Create equipment models**

- `Grinder`: with `dial_type` (StrEnum: stepless/stepped), `display_format`, `ring_sizes_json`
- `Brewer`: full capability model with all enum fields, M2M to BrewMethod + StopMode
- `Paper`: simple name + notes
- `Water` + `WaterMineral`: water with normalized minerals, unique constraint on (water_id, mineral_name)
- Junction tables: `brewer_methods`, `brewer_stop_modes`

Convert capability enums from main to `StrEnum` classes:
`TempControlType`, `PreinfusionType`, `PressureControlType`, `FlowControlType`.

- [ ] **Step 2: Create equipment schemas**

- `GrinderRead` exposes structured `rings: list[RingConfig]` (each with `label`, `min`, `max`, `step`) and computed `grind_range`
- `GrinderCreate`/`GrinderUpdate` accepts `rings` list (with `label`, `min`, `max`, `step`), serializes to `ring_sizes_json`
- `BrewerRead` includes computed `tier`, nested `methods` and `stop_modes`
- `WaterRead` includes nested `minerals` list
- `WaterCreate`/`WaterUpdate` accepts inline `minerals` array

- [ ] **Step 3: Create equipment routers**

- `/grinders` CRUD
- `/brewers` CRUD with M2M management for methods + stop_modes
- `/papers` CRUD
- `/waters` CRUD with mineral delete-and-reinsert on update

- [ ] **Step 4: Write integration tests**

- Grinder CRUD + ring config serialization + structured read
- Brewer CRUD + M2M method/stop_mode management + tier computation
- Paper CRUD (simple)
- Water CRUD + inline mineral create/update/replace

- [ ] **Step 5: Run tests, commit**

```bash
uv run pytest tests/integration/test_equipment_api.py -v
git commit -m "feat: equipment models, schemas, and routers (grinder, brewer, paper, water)"
```

---

## Task 6: Bean + Bag Models + Schemas + Router

**Files:**
- Create: `src/beanbay/models/bean.py`
- Create: `src/beanbay/schemas/bean.py`
- Create: `src/beanbay/routers/beans.py`
- Modify: `src/beanbay/models/__init__.py`
- Modify: `src/beanbay/main.py`
- Test: `tests/integration/test_beans_api.py`

- [ ] **Step 1: Create Bean + Bag models**

- `Bean` with FK to `Roaster`, M2M to Origin/ProcessMethod/BeanVariety
- `Bag` with FK to Bean, `is_preground` flag
- Junction tables: `bean_origins`, `bean_processes`, `bean_varieties`

- [ ] **Step 2: Create Bean + Bag schemas**

- `BeanCreate` accepts `origin_ids`, `process_ids`, `variety_ids`, `roaster_id`
- `BeanRead` includes nested origins, processes, varieties, roaster, and nested bags list.
  `GET /beans/{id}` also returns latest rating per person (query BeanRating ordered by rated_at desc, grouped by person).
- `BagCreate`/`BagRead` with `is_preground`

- [ ] **Step 3: Create `/beans` + `/bags` router**

- `/beans` CRUD with M2M management
- `/beans/{bean_id}/bags` nested list + create
- `/bags` top-level list (filterable by bean_id, is_preground, opened_after)
- `/bags/{id}` direct detail, PATCH, DELETE
- Soft-delete referential integrity: block bean delete if active bags exist

- [ ] **Step 4: Write integration tests**

- Bean CRUD + M2M origin/process/variety
- Bag CRUD nested under bean + top-level access
- Bean with bags — soft-delete behavior
- Filtering: by roaster, origin, preground

- [ ] **Step 5: Run tests, commit**

```bash
uv run pytest tests/integration/test_beans_api.py -v
git commit -m "feat: bean and bag models with M2M relationships and routers"
```

---

## Task 7: BrewSetup Model + Schema + Router

**Files:**
- Create: `src/beanbay/models/brew.py` (BrewSetup only — BrewMethod is in tag.py from Task 2)
- Create: `src/beanbay/schemas/brew.py` (BrewSetup schemas)
- Create: `src/beanbay/routers/brew_setups.py`
- Modify: `src/beanbay/models/__init__.py`
- Modify: `src/beanbay/main.py`
- Test: `tests/integration/test_brew_setups_api.py`

- [ ] **Step 1: Create BrewSetup model**

FK references to BrewMethod, Grinder, Brewer, Paper, Water — all nullable except BrewMethod.

- [ ] **Step 2: Create BrewSetup schemas**

- `BrewSetupRead` with nested equipment names (light nesting)
- `BrewSetupCreate` with FK IDs

- [ ] **Step 3: Create `/brew-setups` router**

- CRUD with filtering by method/grinder/brewer/has_grinder
- Retire (soft-delete), not hard delete

- [ ] **Step 4: Write integration tests**

- Create setup referencing existing equipment
- Filter by has_grinder
- Retire setup

- [ ] **Step 5: Run tests, commit**

```bash
uv run pytest tests/integration/test_brew_setups_api.py -v
git commit -m "feat: brew setup model and router"
```

---

## Task 8: Brew + BrewTaste Models + Schemas + Router

**Files:**
- Modify: `src/beanbay/models/brew.py` (add Brew, BrewTaste)
- Create: `src/beanbay/routers/brews.py`
- Modify: `src/beanbay/schemas/brew.py` (add Brew/BrewTaste schemas)
- Modify: `src/beanbay/models/__init__.py`
- Modify: `src/beanbay/main.py`
- Test: `tests/integration/test_brews_api.py`

- [ ] **Step 1: Create Brew + BrewTaste models**

- Brew with all fields from spec (including pressure, flow_rate, stop_mode_id)
- BrewTaste 1:1 with Brew (unique FK)
- `brew_taste_flavor_tags` junction table

- [ ] **Step 2: Create Brew + BrewTaste schemas**

- `BrewCreate` accepts either `grind_setting` (float) or `grind_setting_display` (str),
  plus an optional nested `taste: BrewTasteCreate | None` for inline taste creation
- `BrewRead` returns both grind representations + full nested data
- `BrewListRead` returns summary nesting (bean name, method name, score)
- `BrewTasteCreate`/`BrewTasteRead` with flavor tag IDs

- [ ] **Step 3: Create `/brews` router**

- CRUD with filtering by person_id/bean_id/bag_id/brew_setup_id/date range
- `PUT /brews/{id}/taste` — create or replace
- `PATCH /brews/{id}/taste` — partial update
- `DELETE /brews/{id}/taste` — remove (204)
- Grind setting conversion: use grinder's ring config via `utils/grinder_display.py`
- List endpoint uses `BrewListRead`, detail uses `BrewRead`

- [ ] **Step 4: Write integration tests**

- Create brew with taste
- Grind setting display conversion round-trip
- PUT/PATCH/DELETE taste
- Filter by person, bean, setup, date range
- List vs detail nesting levels

- [ ] **Step 5: Run tests, commit**

```bash
uv run pytest tests/integration/test_brews_api.py -v
git commit -m "feat: brew and brew taste models with grind display conversion"
```

---

## Task 9: BeanRating + BeanTaste Models + Schemas + Router

**Files:**
- Create: `src/beanbay/models/rating.py`
- Create: `src/beanbay/schemas/rating.py`
- Create: `src/beanbay/routers/ratings.py`
- Modify: `src/beanbay/models/__init__.py`
- Modify: `src/beanbay/main.py`
- Test: `tests/integration/test_ratings_api.py`

- [ ] **Step 1: Create BeanRating + BeanTaste models**

- BeanRating: FK to Bean + Person, `rated_at`, append-only (no unique constraint on bean+person)
- BeanTaste: 1:1 with BeanRating (unique FK)
- `bean_taste_flavor_tags` junction table

- [ ] **Step 2: Create BeanRating + BeanTaste schemas**

- `BeanRatingCreate` with `person_id`, optional inline `taste`
- `BeanRatingRead` with nested taste + tags

- [ ] **Step 3: Create ratings routers**

- `GET /beans/{bean_id}/ratings` with `?person_id=` filter
- `POST /beans/{bean_id}/ratings` (append-only)
- `GET /bean-ratings/{id}`
- `DELETE /bean-ratings/{id}` (soft-delete)
- `PUT/PATCH/DELETE /bean-ratings/{id}/taste`

- [ ] **Step 4: Write integration tests**

- Create rating with taste
- Multiple ratings for same bean+person (append-only)
- Filter by person_id
- PUT/PATCH/DELETE taste

- [ ] **Step 5: Run tests, commit**

```bash
uv run pytest tests/integration/test_ratings_api.py -v
git commit -m "feat: bean rating model with append-only pattern and taste management"
```

---

## Task 10: Unit Conversion (Pint)

**Files:**
- Create: `src/beanbay/utils/units.py`
- Test: `tests/unit/test_unit_conversion.py`

- [ ] **Step 1: Create pint unit conversion helpers**

**IMPORTANT:** Instantiate `UnitRegistry` once at module level. Pint's docs
explicitly recommend this — the registry parses definition files on init and is
expensive to recreate. Use `cache_folder=":auto:"` for faster subsequent startups.

```python
from pint import UnitRegistry

ureg = UnitRegistry(cache_folder=":auto:")
Q_ = ureg.Quantity
```

Functions for:
- `convert_weight(value, from_unit, to_unit)` — grams ↔ oz
- `convert_temperature(value, from_unit, to_unit)` — celsius ↔ fahrenheit
- `convert_pressure(value, from_unit, to_unit)` — bar ↔ psi
- `convert_flow_rate(value, from_unit, to_unit)` — ml/s ↔ fl oz/s

Plus a high-level `apply_unit_conversion(data, unit_system)` that converts
all relevant fields in a response dict.

- [ ] **Step 2: Write unit tests**

- `convert_weight(100, "gram", "ounce")` ≈ 3.527
- `convert_temperature(93, "celsius", "fahrenheit")` ≈ 199.4
- `convert_pressure(9, "bar", "psi")` ≈ 130.5
- Round-trip: metric → imperial → metric

- [ ] **Step 3: Integrate into routers** as a dependency or response middleware

Add `?units=metric|imperial` query param support. Default is metric (no conversion).

- [ ] **Step 4: Run tests, commit**

```bash
uv run pytest tests/unit/test_unit_conversion.py -v
git commit -m "feat: pint-based unit conversion with metric/imperial support"
```

---

## Task 11: Seed Data + Lifespan

**Files:**
- Create: `src/beanbay/seed.py`
- Modify: `src/beanbay/main.py` (lifespan)

- [ ] **Step 1: Create seed functions**

```python
def seed_brew_methods(session: Session) -> None:
    defaults = ["espresso", "pour-over", "french-press",
                "aeropress", "turkish", "moka-pot", "cold-brew"]
    # For each: check if exists by name, create if not

def seed_stop_modes(session: Session) -> None:
    defaults = ["manual", "timed", "volumetric", "gravimetric"]

def seed_default_person(session: Session, name: str) -> None:
    # Create if not exists, set is_default=True
```

All idempotent — safe to run on every startup.

- [ ] **Step 2: Update lifespan in `main.py`**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    from beanbay.database import engine, get_session
    from beanbay.seed import seed_brew_methods, seed_stop_modes, seed_default_person

    # Run Alembic migrations programmatically (Task 12 must be done first)
    from alembic.config import Config as AlembicConfig
    from alembic import command
    alembic_cfg = AlembicConfig("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    with Session(engine) as session:
        seed_brew_methods(session)
        seed_stop_modes(session)
        seed_default_person(session, settings.default_person_name)
        session.commit()
    yield
```

- [ ] **Step 3: Test seeding is idempotent**

Create `tests/integration/test_seed.py`:
Write a test that calls seed functions twice and verifies no duplicates.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: seed brew methods, stop modes, and default person on startup"
```

---

## Task 12: Alembic Setup + Initial Migration

**Files:**
- Create: `migrations/env.py`
- Create: `migrations/script.py.mako`
- Create: `migrations/versions/` (auto-generated)

- [ ] **Step 1: Initialize Alembic migration env**

`migrations/env.py` must:
- Import all models from `beanbay.models` (triggers table registration)
- Use `SQLModel.metadata` as target_metadata
- Read database URL from `beanbay.config.settings`

- [ ] **Step 2: Generate initial migration**

```bash
uv run alembic revision --autogenerate -m "initial schema"
```

Review the generated migration for correctness.

- [ ] **Step 3: Test migration up/down**

```bash
uv run alembic upgrade head
uv run alembic downgrade base
uv run alembic upgrade head
```

- [ ] **Step 4: Commit**

```bash
git add migrations/
git commit -m "feat: Alembic setup with initial schema migration"
```

---

## Task 13: Pagination + Sort Validation Tests

**Files:**
- Test: `tests/integration/test_pagination.py`

- [ ] **Step 1: Write pagination tests**

- Verify `limit`, `offset`, `total` in responses
- Test `limit` > 200 returns 422
- Test `sort_by` with valid field
- Test `sort_by` with invalid field returns 422
- Test `sort_dir` asc/desc
- Test `include_retired` flag

- [ ] **Step 2: Run all tests to verify nothing is broken**

```bash
uv run pytest -v
```

- [ ] **Step 3: Commit**

```bash
git commit -m "test: pagination, sorting, and filtering integration tests"
```

---

## Task 14: Soft-Delete Referential Integrity

**Files:**
- Modify: relevant routers (lookup, beans)

- [ ] **Step 1: Wire `dependent_models` into lookup router factory calls**

The factory already supports `dependent_models` from Task 2. Now fill in the
actual dependencies for each lookup router. For example:
- Origin → `dependent_models=[(bean_origins_table, "origin_id")]` or check via Bean M2M
- FlavorTag → check via BrewTaste and BeanTaste M2M junctions
- Roaster → check via Bean.roaster_id

- [ ] **Step 2: Write tests**

- Cannot soft-delete an Origin that's linked to an active Bean → 409
- Can soft-delete an Origin after unlinking → 200
- Can soft-delete a Person with active brews → 200 (allowed per spec)

- [ ] **Step 3: Run tests, commit**

```bash
uv run pytest -v
git commit -m "feat: soft-delete referential integrity checks (409 Conflict)"
```

---

## Task 15: Final Integration — Full Test Suite

**Files:**
- All test files

- [ ] **Step 1: Run the full test suite**

```bash
uv run pytest -v --tb=short
```

Fix any failures.

- [ ] **Step 2: Verify the OpenAPI spec**

```bash
uv run python -c "from beanbay.main import app; import json; print(json.dumps(app.openapi(), indent=2))" | head -50
```

Verify endpoints are documented correctly.

- [ ] **Step 3: Manual smoke test**

```bash
uv run uvicorn beanbay.main:app --reload
# Visit http://localhost:8000/docs to verify Swagger UI
```

- [ ] **Step 4: Final commit**

```bash
git commit -m "test: complete integration test suite and OpenAPI verification"
```

---

## Execution Order & Dependencies

```
Task 1 (foundation)
├── Task 2 (lookup tables) — depends on 1
├── Task 3 (person) — depends on 1
├── Task 4 (cherry-pick utils) — depends on 1
├── Task 10 (unit conversion) — depends on 1
│
Task 5 (equipment) — depends on 2, 4
Task 6 (bean + bag) — depends on 2
│
Task 7 (brew setup) — depends on 5, 6
Task 8 (brew) — depends on 4, 7, 3
Task 9 (rating) — depends on 2, 3, 6
│
Task 12 (alembic) — depends on all models (5, 6, 8, 9)
Task 11 (seed + lifespan) — depends on 2, 3, 12 (lifespan uses alembic upgrade)
│
Task 13 (pagination tests) — depends on any router
Task 14 (referential integrity) — depends on 6, 2
Task 15 (final integration) — depends on all
```

After Task 1, tasks 2, 3, 4, and 10 can all run in parallel.
After Task 2, tasks 5 and 6 can run in parallel.
Task 11 (seed) can run as soon as Tasks 2 + 3 are done.
