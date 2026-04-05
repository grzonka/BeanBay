# Schema Evolution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enrich BeanBay's database schema with bean metadata, vendor tracking, frozen storage, 3 distinct tasting axis sets, and SCAA cupping support.

**Architecture:** All changes go into the existing SQLModel model layer, Pydantic schema layer, and FastAPI router layer following established patterns. One Alembic migration for the full changeset. TDD with real-database integration tests (no mocks).

**Tech Stack:** SQLModel, FastAPI, Pydantic, Alembic, SQLite, pytest

**Spec:** `docs/superpowers/specs/2026-03-21-schema-evolution-design.md`

---

## File Structure

**New files:**
- `src/beanbay/models/enums.py` — BeanMixType, BeanUseType, ProcessCategory, CoffeeSpecies (bean/process enums separate from equipment enums)
- `src/beanbay/models/cupping.py` — Cupping model + CuppingFlavorTagLink
- `src/beanbay/schemas/cupping.py` — Cupping Create/Update/Read schemas
- `src/beanbay/routers/cuppings.py` — Cupping CRUD router (Vendor uses the lookup factory, no separate router)
- `tests/integration/test_vendors_api.py` — Vendor API tests
- `tests/integration/test_cuppings_api.py` — Cupping API tests

**Modified files:**
- `src/beanbay/models/tag.py` — Origin (+country, region), ProcessMethod (+category), BeanVariety (+species), add Vendor, StorageType
- `src/beanbay/models/bean.py` — Bean (+6 fields, +flavor_tags M2M), Bag (+6 fields), BeanOriginLink (+percentage), BeanFlavorTagLink (new)
- `src/beanbay/models/brew.py` — BrewTaste axis swap
- `src/beanbay/models/rating.py` — BeanRating (+updated_at), BeanTaste axis swap
- `src/beanbay/models/__init__.py` — Re-export new models + enums
- `src/beanbay/schemas/tag.py` — Fix `_compute_is_retired` to be generic, add Origin/ProcessMethod/BeanVariety/Vendor/StorageType schemas
- `src/beanbay/schemas/bean.py` — Bean/Bag schema enrichment, OriginWithPercentage schema
- `src/beanbay/schemas/brew.py` — BrewTaste axis swap
- `src/beanbay/schemas/rating.py` — BeanTaste axis swap, BeanRating +updated_at
- `src/beanbay/seed.py` — Add storage_types seeding
- `src/beanbay/main.py` — Register vendor/cupping/storage_type routers, call seed_storage_types
- `src/beanbay/routers/lookup.py` — Update router instances, add StorageType router, add Vendor via lookup factory
- `src/beanbay/routers/beans.py` — Bean/Bag create/update constructors must include all new fields + flavor_tag M2M + origin percentage handling
- `tests/integration/test_beans_api.py` — Update for new bean/bag fields
- `tests/integration/test_lookup_api.py` — Update for enriched lookup fields
- `tests/integration/test_ratings_api.py` — Update for BeanTaste axis swap
- `tests/integration/test_brews_api.py` — Update for BrewTaste axis swap
- `tests/integration/test_seed.py` — Add storage_types seed test

---

## Critical Implementation Notes

**1. Enum base class:** Use `StrEnum` (not `str, Enum`). Matches existing pattern in `equipment.py`:
```python
from enum import StrEnum
class BeanMixType(StrEnum):
```

**2. `_compute_is_retired` must become generic.** Current helper in `schemas/tag.py` hardcodes field names. Replace with:
```python
def _compute_is_retired(cls: type, data: dict | object) -> dict:
    if isinstance(data, dict):
        data["is_retired"] = data.get("retired_at") is not None
        return data
    data_dict: dict[str, Any] = {}
    for field_name in cls.model_fields:
        if field_name == "is_retired":
            continue
        data_dict[field_name] = getattr(data, field_name, None)
    data_dict["is_retired"] = data_dict.get("retired_at") is not None
    return data_dict
```
This dynamically extracts all fields declared on the Read schema from the ORM object. **Do this first** — all enriched Read schemas depend on it.

**3. Router constructors must pass new fields.** The existing `create_bean` in `routers/beans.py` hardcodes `Bean(name=..., roaster_id=..., notes=...)`. After enrichment, it must also pass `roast_degree`, `bean_mix_type`, `bean_use_type`, `decaf`, `url`, `ean`. Similarly, `create_bag_for_bean` must pass `bought_at`, `vendor_id`, `frozen_at`, `thawed_at`, `storage_type_id`, `best_date`. Consider using `model_validate(payload, exclude={"origin_ids", "flavor_tag_ids", ...})` instead of listing fields individually.

**4. Origin percentage schema design.** Use a typed model instead of a raw union:
```python
class OriginWithPercentage(SQLModel):
    origin_id: uuid.UUID
    percentage: float | None = None

class BeanCreate(BeanBase):
    origin_ids: list[uuid.UUID | OriginWithPercentage] = []
```
In the router, normalize: if element is a UUID, wrap as `OriginWithPercentage(origin_id=uuid, percentage=None)`. When creating `BeanOriginLink`, set `percentage` from the model.

**5. Bag soft-delete must check active Cuppings.** Add to the bag delete handler in `routers/beans.py`:
```python
cupping_count = session.exec(
    select(func.count()).select_from(Cupping)
    .where(Cupping.bag_id == bag_id, Cupping.retired_at.is_(None))
).one()
if cupping_count > 0:
    raise HTTPException(status_code=409, detail=f"Cannot retire bag: {cupping_count} active cupping(s).")
```

**6. Pydantic range validation on schema fields:**
```python
roast_degree: float | None = Field(default=None, ge=0, le=10)  # Bean
score: float | None = Field(default=None, ge=0, le=10)  # BrewTaste/BeanTaste
dry_fragrance: float | None = Field(default=None, ge=0, le=9)  # Cupping
total_score: float | None = Field(default=None, ge=0, le=100)  # Cupping
percentage: float | None = Field(default=None, ge=0, le=100)  # BeanOriginLink
```

---

### Task 1: New Enums + Generic Schema Helper

**Files:**
- Create: `src/beanbay/models/enums.py`
- Modify: `src/beanbay/schemas/tag.py` — Fix `_compute_is_retired` to be generic

- [ ] **Step 1: Create `src/beanbay/models/enums.py`**

```python
"""Domain enums for bean and processing classification."""

from enum import StrEnum


class BeanMixType(StrEnum):
    """Whether a bean is single origin or a blend."""

    SINGLE_ORIGIN = "single_origin"
    BLEND = "blend"
    UNKNOWN = "unknown"


class BeanUseType(StrEnum):
    """Roaster's intended use for the bean."""

    FILTER = "filter"
    ESPRESSO = "espresso"
    OMNI = "omni"


class ProcessCategory(StrEnum):
    """Broad category grouping for coffee processing methods."""

    WASHED = "washed"
    NATURAL = "natural"
    HONEY = "honey"
    ANAEROBIC = "anaerobic"
    EXPERIMENTAL = "experimental"
    OTHER = "other"


class CoffeeSpecies(StrEnum):
    """Biological species of the coffee plant."""

    ARABICA = "arabica"
    ROBUSTA = "robusta"
    LIBERICA = "liberica"
```

- [ ] **Step 2: Make `_compute_is_retired` generic in `schemas/tag.py`**

Replace the current hardcoded helper with the generic version from Critical Implementation Notes above. This must be done **before** any enriched Read schemas are created, as they all depend on it.

- [ ] **Step 3: Verify imports work**

Run: `uv run python -c "from beanbay.models.enums import BeanMixType, BeanUseType, ProcessCategory, CoffeeSpecies; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add src/beanbay/models/enums.py src/beanbay/schemas/tag.py
git commit -m "feat: add domain enums, make _compute_is_retired generic"
```

---

### Task 2: Vendor and StorageType Models

**Files:**
- Modify: `src/beanbay/models/tag.py` — Add Vendor and StorageType models

- [ ] **Step 1: Write integration test for Vendor creation**

Create test in `tests/integration/test_vendors_api.py`:

```python
"""Integration tests for the Vendor API."""

import pytest


class TestVendorCRUD:
    """Basic CRUD tests for the /api/v1/vendors endpoint."""

    def test_create_vendor(self, client):
        resp = client.post(
            "/api/v1/vendors",
            json={"name": "Coffee Island", "url": "https://coffeeisland.example.com", "location": "Athens, Greece"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Coffee Island"
        assert data["url"] == "https://coffeeisland.example.com"
        assert data["location"] == "Athens, Greece"
        assert data["is_retired"] is False

    def test_create_vendor_minimal(self, client):
        resp = client.post("/api/v1/vendors", json={"name": "Local Shop"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["url"] is None
        assert data["location"] is None
        assert data["notes"] is None

    def test_list_vendors(self, client):
        client.post("/api/v1/vendors", json={"name": "Shop A"})
        client.post("/api/v1/vendors", json={"name": "Shop B"})
        resp = client.get("/api/v1/vendors")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 2

    def test_update_vendor(self, client):
        resp = client.post("/api/v1/vendors", json={"name": "Old Name"})
        vid = resp.json()["id"]
        resp = client.patch(f"/api/v1/vendors/{vid}", json={"name": "New Name", "url": "https://new.example.com"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"
        assert resp.json()["url"] == "https://new.example.com"

    def test_delete_vendor(self, client):
        resp = client.post("/api/v1/vendors", json={"name": "To Delete"})
        vid = resp.json()["id"]
        resp = client.delete(f"/api/v1/vendors/{vid}")
        assert resp.status_code == 200
        assert resp.json()["is_retired"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/integration/test_vendors_api.py -v`
Expected: FAIL (no vendor model/routes yet)

- [ ] **Step 3: Add Vendor model to tag.py**

Add at the end of `src/beanbay/models/tag.py`:

```python
class Vendor(SQLModel, table=True):
    """A vendor / shop where beans are purchased.

    Attributes
    ----------
    id : uuid.UUID
        Primary key.
    name : str
        Unique vendor name.
    url : str | None
        Shop website URL.
    location : str | None
        City, address, etc.
    notes : str | None
        Free-text notes.
    created_at : datetime
        Row creation timestamp (server default).
    updated_at : datetime
        Last-modified timestamp (server default, auto-updated).
    retired_at : datetime | None
        Soft-delete timestamp; ``None`` while active.
    """

    __tablename__ = "vendors"  # type: ignore[assignment]

    id: uuid.UUID = Field(default_factory=uuid4_default, primary_key=True)
    name: str = Field(index=True, unique=True)
    url: str | None = None
    location: str | None = None
    notes: str | None = None
    created_at: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": func.now()},
    )
    updated_at: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()},
    )
    retired_at: datetime | None = None
```

- [ ] **Step 4: Add StorageType model to tag.py**

Add after Vendor in `src/beanbay/models/tag.py`:

```python
class StorageType(SQLModel, table=True):
    """A frozen storage type (e.g. 'Vacuum Sealed', 'Zip Lock').

    Attributes
    ----------
    id : uuid.UUID
        Primary key.
    name : str
        Unique storage type name.
    created_at : datetime
        Row creation timestamp (server default).
    updated_at : datetime
        Last-modified timestamp (server default, auto-updated).
    retired_at : datetime | None
        Soft-delete timestamp; ``None`` while active.
    """

    __tablename__ = "storage_types"  # type: ignore[assignment]

    id: uuid.UUID = Field(default_factory=uuid4_default, primary_key=True)
    name: str = Field(index=True, unique=True)
    created_at: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": func.now()},
    )
    updated_at: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()},
    )
    retired_at: datetime | None = None
```

- [ ] **Step 5: Add Vendor and StorageType schemas to schemas/tag.py**

Add Vendor schemas (Base/Create/Update/Read) and StorageType schemas following the existing pattern. Vendor's `_compute_is_retired` helper must also extract `url`, `location`, `notes`, `updated_at` fields. StorageType schemas follow the standard lookup pattern but include `updated_at` in Read.

- [ ] **Step 6: Add Vendor router via lookup factory**

The `create_lookup_router` factory's `model_validate(payload)` call handles arbitrary fields — Vendor's extra fields (`url`, `location`, `notes`) work without modification. Use the factory:

```python
vendor_router = create_lookup_router(
    model_class=Vendor,
    create_schema=VendorCreate,
    update_schema=VendorUpdate,
    read_schema=VendorRead,
    prefix="vendors",
    tag="Vendors",
    sortable_fields=["name", "location", "created_at"],
    dependency_checks=[],  # Add bag check in Task 5
)
```

- [ ] **Step 7: Add StorageType router via lookup factory**

Add to `src/beanbay/routers/lookup.py`:

```python
from beanbay.models.tag import StorageType, Vendor
from beanbay.schemas.tag import (
    StorageTypeCreate, StorageTypeRead, StorageTypeUpdate,
    VendorCreate, VendorRead, VendorUpdate,
)

storage_type_router = create_lookup_router(
    model_class=StorageType,
    create_schema=StorageTypeCreate,
    update_schema=StorageTypeUpdate,
    read_schema=StorageTypeRead,
    prefix="storage-types",
    tag="Storage Types",
    dependency_checks=[
        ("bags", _fk_active_count(Bag, "storage_type_id")),
    ],
)
```

Note: The Bag import and `storage_type_id` FK won't exist yet — add the dependency check later in Task 6 when Bag is updated. For now, create without dependency_checks.

- [ ] **Step 8: Register routers in main.py**

Import and add the vendor and storage_type routers to the `_routers` list in `src/beanbay/main.py`.

- [ ] **Step 9: Update models/__init__.py**

Add `Vendor` and `StorageType` to the imports from `beanbay.models.tag`.

- [ ] **Step 10: Run vendor tests**

Run: `uv run pytest tests/integration/test_vendors_api.py -v`
Expected: ALL PASS

- [ ] **Step 11: Commit**

```bash
git add src/beanbay/models/tag.py src/beanbay/schemas/tag.py src/beanbay/routers/lookup.py src/beanbay/main.py src/beanbay/models/__init__.py tests/integration/test_vendors_api.py
git commit -m "feat: add Vendor and StorageType entities with CRUD endpoints"
```

---

### Task 3: Lookup Table Model Enrichment

**Files:**
- Modify: `src/beanbay/models/tag.py` — Origin, ProcessMethod, BeanVariety
- Modify: `src/beanbay/schemas/tag.py` — Updated schemas
- Modify: `src/beanbay/routers/lookup.py` — Updated sortable_fields

- [ ] **Step 1: Write test for enriched Origin**

Add to `tests/integration/test_lookup_api.py` (or new test class):

```python
class TestOriginEnrichment:
    def test_create_origin_with_country_region(self, client):
        resp = client.post(
            "/api/v1/origins",
            json={"name": "Yirgacheffe", "country": "Ethiopia", "region": "Sidamo"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["country"] == "Ethiopia"
        assert data["region"] == "Sidamo"

    def test_create_origin_minimal(self, client):
        resp = client.post("/api/v1/origins", json={"name": "Brazil"})
        assert resp.status_code == 201
        assert resp.json()["country"] is None
        assert resp.json()["region"] is None
```

- [ ] **Step 2: Run test to verify failure**

Run: `uv run pytest tests/integration/test_lookup_api.py::TestOriginEnrichment -v`
Expected: FAIL

- [ ] **Step 3: Add fields to Origin model**

In `src/beanbay/models/tag.py`, add to the `Origin` class (before `created_at`):

```python
    country: str | None = None
    region: str | None = None
```

- [ ] **Step 4: Add `category` to ProcessMethod model**

In `src/beanbay/models/tag.py`, add to `ProcessMethod` (before `created_at`):

```python
    category: ProcessCategory | None = None
```

Add import at top: `from beanbay.models.enums import ProcessCategory, CoffeeSpecies`

- [ ] **Step 5: Add `species` to BeanVariety model**

In `src/beanbay/models/tag.py`, add to `BeanVariety` (before `created_at`):

```python
    species: CoffeeSpecies | None = None
```

- [ ] **Step 6: Update Origin/ProcessMethod/BeanVariety schemas**

In `src/beanbay/schemas/tag.py`:

- `OriginBase` — add `country: str | None = None`, `region: str | None = None`
- `OriginCreate` — inherits from OriginBase (gets country/region automatically)
- `OriginUpdate` — add `country: str | None = None`, `region: str | None = None`
- `OriginRead` — fields are inherited; update `_compute_is_retired` helper or the ORM extractor to also extract `country` and `region`

Similarly for ProcessMethod (add `category`) and BeanVariety (add `species`). The Read schemas need the enum imports and the ORM field extraction updated.

**Important:** The shared `_compute_is_retired` helper in tag.py currently hardcodes `("id", "name", "created_at", "retired_at")`. It won't extract `country`, `region`, `category`, `species`, `url`, `location`, `notes`, `updated_at`. Either:
- (a) Make the helper generic by extracting all fields from `cls.model_fields`, or
- (b) Override the validator in enriched Read schemas to extract extra fields.

Option (a) is cleaner. Update `_compute_is_retired` to use `cls.model_fields.keys()` instead of a hardcoded tuple.

- [ ] **Step 7: Update lookup router sortable_fields**

In `src/beanbay/routers/lookup.py`, update the `origin_router` to include `sortable_fields=["name", "country", "created_at"]`.

- [ ] **Step 8: Run enrichment tests**

Run: `uv run pytest tests/integration/test_lookup_api.py -v`
Expected: ALL PASS

- [ ] **Step 9: Commit**

```bash
git add src/beanbay/models/tag.py src/beanbay/schemas/tag.py src/beanbay/routers/lookup.py tests/integration/test_lookup_api.py
git commit -m "feat: enrich Origin, ProcessMethod, BeanVariety with structured fields"
```

---

### Task 4: Bean Model Enrichment

**Files:**
- Modify: `src/beanbay/models/bean.py` — Bean (+fields, +BeanFlavorTagLink), BeanOriginLink (+percentage)
- Modify: `src/beanbay/schemas/bean.py` — BeanCreate/Update/Read enrichment
- Modify: `src/beanbay/routers/beans.py` — Handle new fields + flavor_tag_ids M2M
- Modify: `src/beanbay/models/__init__.py` — Export BeanFlavorTagLink

- [ ] **Step 1: Write test for enriched Bean creation**

Add to `tests/integration/test_beans_api.py`:

```python
class TestBeanEnrichment:
    def test_create_bean_with_new_fields(self, client):
        resp = client.post("/api/v1/beans", json={
            "name": "Ethiopia Guji",
            "roast_degree": 4.5,
            "bean_mix_type": "single_origin",
            "bean_use_type": "filter",
            "decaf": False,
            "url": "https://roaster.example.com/guji",
            "ean": "4012345678901",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["roast_degree"] == 4.5
        assert data["bean_mix_type"] == "single_origin"
        assert data["bean_use_type"] == "filter"
        assert data["decaf"] is False
        assert data["url"] == "https://roaster.example.com/guji"
        assert data["ean"] == "4012345678901"

    def test_create_bean_defaults(self, client):
        resp = client.post("/api/v1/beans", json={"name": "Simple Bean"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["roast_degree"] is None
        assert data["bean_mix_type"] == "unknown"
        assert data["bean_use_type"] is None
        assert data["decaf"] is False

    def test_create_bean_with_flavor_tags(self, client):
        tag1 = client.post("/api/v1/flavor-tags", json={"name": "cherry"}).json()
        tag2 = client.post("/api/v1/flavor-tags", json={"name": "chocolate"}).json()
        resp = client.post("/api/v1/beans", json={
            "name": "Flavor Tagged Bean",
            "flavor_tag_ids": [tag1["id"], tag2["id"]],
        })
        assert resp.status_code == 201
        data = resp.json()
        tag_names = {t["name"] for t in data["flavor_tags"]}
        assert tag_names == {"cherry", "chocolate"}

    def test_bean_origin_with_percentage(self, client):
        origin = client.post("/api/v1/origins", json={"name": "Colombia"}).json()
        resp = client.post("/api/v1/beans", json={
            "name": "Blend Bean",
            "bean_mix_type": "blend",
            "origins": [{"origin_id": origin["id"], "percentage": 60.0}],
        })
        assert resp.status_code == 201
        origins = resp.json()["origins"]
        assert len(origins) == 1
        assert origins[0]["percentage"] == 60.0

    def test_bean_origin_plain_ids_still_works(self, client):
        """Backwards compat: plain UUID list still accepted."""
        origin = client.post("/api/v1/origins", json={"name": "Kenya"}).json()
        resp = client.post("/api/v1/beans", json={
            "name": "Plain Origin Bean",
            "origin_ids": [origin["id"]],
        })
        assert resp.status_code == 201
        assert len(resp.json()["origins"]) == 1
        assert resp.json()["origins"][0]["percentage"] is None
```

- [ ] **Step 2: Run tests to verify failure**

Run: `uv run pytest tests/integration/test_beans_api.py::TestBeanEnrichment -v`
Expected: FAIL

- [ ] **Step 3: Add BeanFlavorTagLink to bean.py**

Add new junction table in `src/beanbay/models/bean.py`:

```python
class BeanFlavorTagLink(SQLModel, table=True):
    """Link table between Bean and FlavorTag (roaster's claimed flavors).

    Attributes
    ----------
    bean_id : uuid.UUID
        Foreign key to the bean.
    flavor_tag_id : uuid.UUID
        Foreign key to the flavor tag.
    """

    __tablename__ = "bean_flavor_tags"  # type: ignore[assignment]

    bean_id: uuid.UUID = Field(foreign_key="beans.id", primary_key=True)
    flavor_tag_id: uuid.UUID = Field(foreign_key="flavor_tags.id", primary_key=True)
```

- [ ] **Step 4: Add percentage to BeanOriginLink**

In `src/beanbay/models/bean.py`, add to `BeanOriginLink`:

```python
    percentage: float | None = None
```

- [ ] **Step 5: Add new fields to Bean model**

In `src/beanbay/models/bean.py`, add to the `Bean` class (after `notes`):

```python
    roast_degree: float | None = None
    bean_mix_type: BeanMixType = Field(default=BeanMixType.UNKNOWN)
    bean_use_type: BeanUseType | None = None
    decaf: bool = Field(default=False)
    url: str | None = None
    ean: str | None = None
```

Add import: `from beanbay.models.enums import BeanMixType, BeanUseType`

Add relationship to Bean:

```python
    flavor_tags: list["FlavorTag"] = Relationship(  # type: ignore[name-defined]  # noqa: F821
        link_model=BeanFlavorTagLink,
    )
```

- [ ] **Step 6: Update Bean schemas**

In `src/beanbay/schemas/bean.py`:

- `BeanBase` — add `roast_degree`, `bean_mix_type`, `bean_use_type`, `decaf`, `url`, `ean` with appropriate defaults
- `BeanCreate` — add `flavor_tag_ids: list[uuid.UUID] = []`. Add new field `origins: list[OriginWithPercentage] = []` for origins with percentages. Keep `origin_ids: list[uuid.UUID] = []` for backwards compat (plain UUIDs, no percentage). In the router, merge both: plain `origin_ids` become `OriginWithPercentage(origin_id=x, percentage=None)`. Define in `schemas/bean.py`:
  ```python
  class OriginWithPercentage(SQLModel):
      origin_id: uuid.UUID
      percentage: float | None = Field(default=None, ge=0, le=100)
  ```
- `BeanUpdate` — add all new optional fields + `flavor_tag_ids: list[uuid.UUID] | None = None` + `origins: list[OriginWithPercentage] | None = None`
- `BeanRead` — add new fields + `flavor_tags: list[FlavorTagRead] = []`, update ORM field extractor

- [ ] **Step 7: Update beans router**

In `src/beanbay/routers/beans.py`:

- Update `_set_bean_m2m` to handle `flavor_tag_ids` (add/replace `BeanFlavorTagLink` rows)
- Update origin handling to support percentage in `BeanOriginLink`
- Add `flavor_tag_ids` validation (check tags exist + not retired)
- Update list endpoint to support filtering by `bean_mix_type`, `decaf`

- [ ] **Step 8: Update models/__init__.py**

Add `BeanFlavorTagLink` to imports from `beanbay.models.bean`.

- [ ] **Step 9: Run bean enrichment tests**

Run: `uv run pytest tests/integration/test_beans_api.py -v`
Expected: ALL PASS

- [ ] **Step 10: Commit**

```bash
git add src/beanbay/models/bean.py src/beanbay/schemas/bean.py src/beanbay/routers/beans.py src/beanbay/models/__init__.py tests/integration/test_beans_api.py
git commit -m "feat: enrich Bean model with roast_degree, mix_type, flavor_tags, origin percentages"
```

---

### Task 5: Bag Model Enrichment

**Files:**
- Modify: `src/beanbay/models/bean.py` — Bag (+fields)
- Modify: `src/beanbay/schemas/bean.py` — Bag schema enrichment
- Modify: `src/beanbay/routers/beans.py` — Bag create/update with new fields

- [ ] **Step 1: Write test for enriched Bag**

Add to `tests/integration/test_beans_api.py`:

```python
class TestBagEnrichment:
    def _create_bean(self, client):
        return client.post("/api/v1/beans", json={"name": "Test Bean"}).json()["id"]

    def test_create_bag_with_new_fields(self, client):
        bean_id = self._create_bean(client)
        vendor = client.post("/api/v1/vendors", json={"name": "Test Shop"}).json()
        storage = client.post("/api/v1/storage-types", json={"name": "Vacuum Sealed"}).json()
        resp = client.post(f"/api/v1/beans/{bean_id}/bags", json={
            "weight": 250.0,
            "bought_at": "2026-03-20",
            "vendor_id": vendor["id"],
            "frozen_at": "2026-03-20T10:00:00",
            "storage_type_id": storage["id"],
            "best_date": "2026-06-20",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["bought_at"] == "2026-03-20"
        assert data["vendor_id"] == vendor["id"]
        assert data["frozen_at"] is not None
        assert data["storage_type_id"] == storage["id"]
        assert data["best_date"] == "2026-06-20"
        assert data["thawed_at"] is None
```

- [ ] **Step 2: Run test to verify failure**

Run: `uv run pytest tests/integration/test_beans_api.py::TestBagEnrichment -v`
Expected: FAIL

- [ ] **Step 3: Add new fields to Bag model**

In `src/beanbay/models/bean.py`, add to `Bag` (after `notes`):

```python
    bought_at: date | None = None
    vendor_id: uuid.UUID | None = Field(default=None, foreign_key="vendors.id")
    frozen_at: datetime | None = None
    thawed_at: datetime | None = None
    storage_type_id: uuid.UUID | None = Field(default=None, foreign_key="storage_types.id")
    best_date: date | None = None
```

Add `datetime` to the imports if not already there. Add relationships:

```python
    vendor: Optional["Vendor"] = Relationship()  # type: ignore[name-defined]  # noqa: F821
    storage_type: Optional["StorageType"] = Relationship()  # type: ignore[name-defined]  # noqa: F821
```

- [ ] **Step 4: Update Bag schemas**

In `src/beanbay/schemas/bean.py`:

- `BagBase` — add `bought_at`, `vendor_id`, `frozen_at`, `thawed_at`, `storage_type_id`, `best_date` with nullable defaults
- `BagUpdate` — add all new fields as optional
- `BagRead` — add new fields + update ORM field extractor to include them

- [ ] **Step 5: Run bag tests**

Run: `uv run pytest tests/integration/test_beans_api.py::TestBagEnrichment -v`
Expected: PASS

- [ ] **Step 6: Update StorageType router dependency check**

Now that Bag has `storage_type_id`, update the `storage_type_router` in `src/beanbay/routers/lookup.py` to add the dependency check:

```python
storage_type_router = create_lookup_router(
    ...,
    dependency_checks=[
        ("bags", _fk_active_count(Bag, "storage_type_id")),
    ],
)
```

Add the `Bag` import from `beanbay.models.bean`.

- [ ] **Step 7: Commit**

```bash
git add src/beanbay/models/bean.py src/beanbay/schemas/bean.py src/beanbay/routers/beans.py src/beanbay/routers/lookup.py tests/integration/test_beans_api.py
git commit -m "feat: enrich Bag with vendor, frozen storage, bought_at, best_date"
```

---

### Task 6: BrewTaste Axis Rework

**Files:**
- Modify: `src/beanbay/models/brew.py` — BrewTaste axis swap
- Modify: `src/beanbay/schemas/brew.py` — BrewTaste schema axis swap

- [ ] **Step 1: Write test for new BrewTaste axes**

Add to `tests/integration/test_brews_api.py`:

```python
class TestBrewTasteAxisRework:
    def test_brew_taste_has_balance_and_aftertaste(self, client, ...):
        # Create prerequisite resources (bean, bag, brew_setup, person, brew)
        # Then verify taste axes
        brew = ...  # create brew with taste
        taste = brew["taste"]
        assert "balance" in taste
        assert "aftertaste" in taste
        assert "intensity" not in taste
        assert "aroma" not in taste
```

This test needs the full brew creation chain. Use existing test helpers from the file.

- [ ] **Step 2: Update BrewTaste model**

In `src/beanbay/models/brew.py`, replace the BrewTaste score fields:

Remove: `aroma`, `intensity`
Add: `balance`, `aftertaste`

```python
    score: float | None = None
    acidity: float | None = None
    sweetness: float | None = None
    bitterness: float | None = None
    body: float | None = None
    balance: float | None = None
    aftertaste: float | None = None
    notes: str | None = None
```

Update the docstring accordingly.

- [ ] **Step 3: Update BrewTaste schemas**

In `src/beanbay/schemas/brew.py`, update `BrewTasteBase`, `BrewTasteCreate`, `BrewTasteUpdate`, and `BrewTasteRead`:

Remove: `aroma`, `intensity` fields
Add: `balance`, `aftertaste` fields

Update the ORM field extractor in `BrewTasteRead.extract_taste_fields` to list the new field names.

- [ ] **Step 4: Update existing BrewTaste tests**

Any existing tests in `test_brews_api.py` that reference `aroma` or `intensity` must be updated to use `balance` and `aftertaste`.

- [ ] **Step 5: Run brew tests**

Run: `uv run pytest tests/integration/test_brews_api.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add src/beanbay/models/brew.py src/beanbay/schemas/brew.py tests/integration/test_brews_api.py
git commit -m "feat: rework BrewTaste axes — replace aroma/intensity with balance/aftertaste"
```

---

### Task 7: BeanTaste Axis Rework + BeanRating updated_at

**Files:**
- Modify: `src/beanbay/models/rating.py` — BeanTaste axis swap, BeanRating +updated_at
- Modify: `src/beanbay/schemas/rating.py` — BeanTaste/BeanRating schema updates

- [ ] **Step 1: Write test for new BeanTaste axes and BeanRating updated_at**

Add to `tests/integration/test_ratings_api.py`:

```python
class TestBeanTasteAxisRework:
    def test_bean_taste_has_complexity_and_clean_cup(self, client, ...):
        # Create bean + rating with taste
        rating = ...
        taste = rating["taste"]
        assert "complexity" in taste
        assert "clean_cup" in taste
        assert "bitterness" not in taste
        assert "intensity" not in taste

class TestBeanRatingUpdatedAt:
    def test_bean_rating_has_updated_at(self, client, ...):
        # Create bean + rating
        rating = ...
        assert "updated_at" in rating
```

- [ ] **Step 2: Update BeanRating model**

In `src/beanbay/models/rating.py`, add `updated_at` to `BeanRating` (after `created_at`):

```python
    updated_at: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()},
    )
```

Update the docstring to remove "No `updated_at` column" note.

- [ ] **Step 3: Update BeanTaste model**

In `src/beanbay/models/rating.py`, replace BeanTaste score fields:

Remove: `bitterness`, `intensity`
Add: `complexity`, `clean_cup`

```python
    score: float | None = None
    acidity: float | None = None
    sweetness: float | None = None
    body: float | None = None
    aroma: float | None = None
    complexity: float | None = None
    clean_cup: float | None = None
    notes: str | None = None
```

- [ ] **Step 4: Update rating schemas**

In `src/beanbay/schemas/rating.py`:

- `BeanTasteBase` — remove `bitterness`, `intensity`; add `complexity`, `clean_cup`
- `BeanTasteUpdate` — same swap
- `BeanTasteRead` — update ORM field extractor
- `BeanRatingRead` — add `updated_at: datetime` field, update ORM extractor

- [ ] **Step 5: Update existing rating tests**

Any existing tests referencing `bitterness` or `intensity` on BeanTaste must be updated.

- [ ] **Step 6: Run rating tests**

Run: `uv run pytest tests/integration/test_ratings_api.py -v`
Expected: ALL PASS

- [ ] **Step 7: Commit**

```bash
git add src/beanbay/models/rating.py src/beanbay/schemas/rating.py tests/integration/test_ratings_api.py
git commit -m "feat: rework BeanTaste axes, add updated_at to BeanRating"
```

---

### Task 8: Cupping Entity

**Files:**
- Create: `src/beanbay/models/cupping.py`
- Create: `src/beanbay/schemas/cupping.py`
- Create: `src/beanbay/routers/cuppings.py`
- Create: `tests/integration/test_cuppings_api.py`
- Modify: `src/beanbay/models/__init__.py`
- Modify: `src/beanbay/main.py`

- [ ] **Step 1: Write integration tests for Cupping CRUD**

Create `tests/integration/test_cuppings_api.py`:

```python
"""Integration tests for the Cupping API."""


def _setup_bag(client):
    """Create a bean + bag and return the bag_id."""
    bean = client.post("/api/v1/beans", json={"name": "Cupping Bean"}).json()
    bag = client.post(
        f"/api/v1/beans/{bean['id']}/bags", json={"weight": 250.0}
    ).json()
    return bag["id"]


def _setup_person(client):
    """Create a person and return the person_id."""
    resp = client.post("/api/v1/people", json={"name": "Cupper"})
    return resp.json()["id"]


class TestCuppingCRUD:
    def test_create_cupping(self, client):
        bag_id = _setup_bag(client)
        person_id = _setup_person(client)
        resp = client.post("/api/v1/cuppings", json={
            "bag_id": bag_id,
            "person_id": person_id,
            "cupped_at": "2026-03-21T10:00:00",
            "dry_fragrance": 7.5,
            "wet_aroma": 8.0,
            "brightness": 7.0,
            "flavor": 8.5,
            "body": 7.0,
            "finish": 7.5,
            "sweetness": 8.0,
            "clean_cup": 8.5,
            "complexity": 7.5,
            "uniformity": 8.0,
            "cuppers_correction": 0.5,
            "total_score": 85.0,
            "notes": "Excellent cup",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["dry_fragrance"] == 7.5
        assert data["total_score"] == 85.0
        assert data["bag_id"] == bag_id

    def test_create_cupping_minimal(self, client):
        bag_id = _setup_bag(client)
        person_id = _setup_person(client)
        resp = client.post("/api/v1/cuppings", json={
            "bag_id": bag_id,
            "person_id": person_id,
            "cupped_at": "2026-03-21T10:00:00",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["dry_fragrance"] is None
        assert data["total_score"] is None

    def test_create_cupping_with_flavor_tags(self, client):
        bag_id = _setup_bag(client)
        person_id = _setup_person(client)
        tag = client.post("/api/v1/flavor-tags", json={"name": "berry"}).json()
        resp = client.post("/api/v1/cuppings", json={
            "bag_id": bag_id,
            "person_id": person_id,
            "cupped_at": "2026-03-21T10:00:00",
            "flavor_tag_ids": [tag["id"]],
        })
        assert resp.status_code == 201
        assert len(resp.json()["flavor_tags"]) == 1

    def test_list_cuppings_for_bag(self, client):
        bag_id = _setup_bag(client)
        person_id = _setup_person(client)
        client.post("/api/v1/cuppings", json={
            "bag_id": bag_id, "person_id": person_id,
            "cupped_at": "2026-03-21T10:00:00",
        })
        client.post("/api/v1/cuppings", json={
            "bag_id": bag_id, "person_id": person_id,
            "cupped_at": "2026-03-22T10:00:00",
        })
        resp = client.get(f"/api/v1/cuppings?bag_id={bag_id}")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 2

    def test_update_cupping(self, client):
        bag_id = _setup_bag(client)
        person_id = _setup_person(client)
        cupping = client.post("/api/v1/cuppings", json={
            "bag_id": bag_id, "person_id": person_id,
            "cupped_at": "2026-03-21T10:00:00",
            "dry_fragrance": 7.0,
        }).json()
        resp = client.patch(
            f"/api/v1/cuppings/{cupping['id']}",
            json={"dry_fragrance": 8.0, "notes": "Adjusted"},
        )
        assert resp.status_code == 200
        assert resp.json()["dry_fragrance"] == 8.0
        assert resp.json()["notes"] == "Adjusted"

    def test_delete_cupping(self, client):
        bag_id = _setup_bag(client)
        person_id = _setup_person(client)
        cupping = client.post("/api/v1/cuppings", json={
            "bag_id": bag_id, "person_id": person_id,
            "cupped_at": "2026-03-21T10:00:00",
        }).json()
        resp = client.delete(f"/api/v1/cuppings/{cupping['id']}")
        assert resp.status_code == 200
        assert resp.json()["is_retired"] is True
```

- [ ] **Step 2: Run tests to verify failure**

Run: `uv run pytest tests/integration/test_cuppings_api.py -v`
Expected: FAIL

- [ ] **Step 3: Create Cupping model**

Create `src/beanbay/models/cupping.py`:

```python
"""Cupping model for SCAA-protocol coffee evaluations."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import func
from sqlmodel import Field, Relationship, SQLModel

from beanbay.models.base import uuid4_default

if TYPE_CHECKING:
    from beanbay.models.bean import Bag
    from beanbay.models.person import Person
    from beanbay.models.tag import FlavorTag


class CuppingFlavorTagLink(SQLModel, table=True):
    """Link table between Cupping and FlavorTag."""

    __tablename__ = "cupping_flavor_tags"  # type: ignore[assignment]

    cupping_id: uuid.UUID = Field(foreign_key="cuppings.id", primary_key=True)
    flavor_tag_id: uuid.UUID = Field(foreign_key="flavor_tags.id", primary_key=True)


class Cupping(SQLModel, table=True):
    """An SCAA-protocol cupping evaluation of a bag of coffee.

    Attributes
    ----------
    id : uuid.UUID
        Primary key.
    bag_id : uuid.UUID
        Foreign key to the bag being cupped.
    person_id : uuid.UUID
        Foreign key to the person who cupped.
    cupped_at : datetime
        When the cupping session happened.
    dry_fragrance : float | None
        Ground coffee aroma (0-9 SCAA).
    wet_aroma : float | None
        Aroma after adding water (0-9).
    brightness : float | None
        Acidity / vibrancy (0-9).
    flavor : float | None
        Overall taste quality (0-9).
    body : float | None
        Weight / mouthfeel (0-9).
    finish : float | None
        Aftertaste length and quality (0-9).
    sweetness : float | None
        Sweetness (0-9).
    clean_cup : float | None
        Absence of defects (0-9).
    complexity : float | None
        Flavor layers / depth (0-9).
    uniformity : float | None
        Cup-to-cup consistency (0-9).
    cuppers_correction : float | None
        Personal adjustment (can be negative).
    total_score : float | None
        0-100 SCAA scale.
    notes : str | None
        Free-text notes.
    created_at : datetime
        Row creation timestamp (server default).
    updated_at : datetime
        Last-modified timestamp (server default, auto-updated).
    retired_at : datetime | None
        Soft-delete timestamp; ``None`` while active.
    """

    __tablename__ = "cuppings"  # type: ignore[assignment]

    id: uuid.UUID = Field(default_factory=uuid4_default, primary_key=True)
    bag_id: uuid.UUID = Field(foreign_key="bags.id")
    person_id: uuid.UUID = Field(foreign_key="people.id")
    cupped_at: datetime

    dry_fragrance: float | None = None
    wet_aroma: float | None = None
    brightness: float | None = None
    flavor: float | None = None
    body: float | None = None
    finish: float | None = None
    sweetness: float | None = None
    clean_cup: float | None = None
    complexity: float | None = None
    uniformity: float | None = None
    cuppers_correction: float | None = None
    total_score: float | None = None
    notes: str | None = None

    created_at: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": func.now()},
    )
    updated_at: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()},
    )
    retired_at: datetime | None = None

    # Relationships
    bag: "Bag" = Relationship()  # type: ignore[name-defined]  # noqa: F821
    person: "Person" = Relationship()  # type: ignore[name-defined]  # noqa: F821
    flavor_tags: list["FlavorTag"] = Relationship(  # type: ignore[name-defined]  # noqa: F821
        link_model=CuppingFlavorTagLink,
    )
```

- [ ] **Step 4: Create Cupping schemas**

Create `src/beanbay/schemas/cupping.py` with `CuppingCreate`, `CuppingUpdate`, `CuppingRead` following the established pattern. `CuppingCreate` takes `bag_id`, `person_id`, `cupped_at`, all 11 SCAA axes (nullable), `total_score`, `notes`, `flavor_tag_ids`. `CuppingRead` includes nested `flavor_tags`, `is_retired`, `person_name`.

- [ ] **Step 5: Create Cupping router**

Create `src/beanbay/routers/cuppings.py` with:
- `POST /cuppings` — create (validate bag_id, person_id, flavor_tag_ids exist)
- `GET /cuppings` — list with filtering by `bag_id`, `person_id`, pagination, sorting
- `GET /cuppings/{id}` — detail
- `PATCH /cuppings/{id}` — partial update
- `DELETE /cuppings/{id}` — soft-delete

Follow the same pattern as the brews router.

- [ ] **Step 6: Update models/__init__.py**

Add imports for `Cupping` and `CuppingFlavorTagLink` from `beanbay.models.cupping`.

- [ ] **Step 7: Register cupping router in main.py**

Import and add the cupping router to the `_routers` list.

- [ ] **Step 8: Run cupping tests**

Run: `uv run pytest tests/integration/test_cuppings_api.py -v`
Expected: ALL PASS

- [ ] **Step 9: Commit**

```bash
git add src/beanbay/models/cupping.py src/beanbay/schemas/cupping.py src/beanbay/routers/cuppings.py src/beanbay/models/__init__.py src/beanbay/main.py tests/integration/test_cuppings_api.py
git commit -m "feat: add Cupping entity with SCAA-protocol axes and CRUD endpoints"
```

---

### Task 9: Seed Data + FlavorTag Dependency Update

**Files:**
- Modify: `src/beanbay/seed.py` — Add storage_types seeding
- Modify: `src/beanbay/main.py` — Call new seed function
- Modify: `src/beanbay/routers/lookup.py` — Add FlavorTag dependency check for bean_flavor_tags and cupping_flavor_tags

- [ ] **Step 1: Write seed test**

Add to `tests/integration/test_seed.py`:

```python
def test_seed_storage_types(session):
    from beanbay.seed import seed_storage_types
    seed_storage_types(session)
    session.commit()
    from beanbay.models.tag import StorageType
    from sqlmodel import select
    types = session.exec(select(StorageType)).all()
    names = {t.name for t in types}
    assert {"Vacuum Sealed", "Zip Lock", "Coffee Bag", "Coffee Jar", "Tube"} <= names
```

- [ ] **Step 2: Add seed_storage_types function**

In `src/beanbay/seed.py`:

```python
from beanbay.models.tag import StorageType

def seed_storage_types(session: Session) -> None:
    """Insert default storage types if they do not already exist."""
    defaults = ["Vacuum Sealed", "Zip Lock", "Coffee Bag", "Coffee Jar", "Tube"]
    for name in defaults:
        existing = session.exec(
            select(StorageType).where(StorageType.name == name)
        ).first()
        if not existing:
            session.add(StorageType(name=name))
```

- [ ] **Step 3: Call seed in main.py lifespan**

Add `seed_storage_types(session)` call in the lifespan handler, after the existing seed calls.

- [ ] **Step 4: Update FlavorTag dependency checks**

In `src/beanbay/routers/lookup.py`, add dependency checks for `bean_flavor_tags` and `cupping_flavor_tags` to the `flavor_tag_router`:

```python
from beanbay.models.bean import BeanFlavorTagLink
from beanbay.models.cupping import Cupping, CuppingFlavorTagLink

# Add two new checks to the existing flavor_tag_router dependency_checks list:
flavor_tag_router = create_lookup_router(
    ...,
    dependency_checks=[
        # ... keep existing brew_taste and bean_taste checks ...
        (
            "bean_flavor_tags",
            _m2m_active_count(
                BeanFlavorTagLink, "flavor_tag_id", Bean, "bean_id"
            ),
        ),
        (
            "cupping_flavor_tags",
            _m2m_active_count(
                CuppingFlavorTagLink, "flavor_tag_id", Cupping, "cupping_id"
            ),
        ),
    ],
)
```

Cupping has `retired_at` directly, so `_m2m_active_count` is correct (not grandparent).

Also update the `vendor_router` dependency_checks to block deletion when bags reference the vendor:

```python
vendor_router = create_lookup_router(
    ...,
    dependency_checks=[
        ("bags", _fk_active_count(Bag, "vendor_id")),
    ],
)
```

- [ ] **Step 5: Run seed + dependency tests**

Run: `uv run pytest tests/integration/test_seed.py tests/integration/test_soft_delete_integrity.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add src/beanbay/seed.py src/beanbay/main.py src/beanbay/routers/lookup.py tests/integration/test_seed.py
git commit -m "feat: seed storage types, update FlavorTag dependency checks"
```

---

### Task 10: Alembic Migration

**Files:**
- Create: `migrations/versions/xxxx_schema_evolution.py` (auto-generated)
- Delete: `migrations/versions/82cc9e91963b_initial_schema.py` (replace with fresh initial)

Since this is development-phase with no production data, the simplest approach is to regenerate the initial migration.

- [ ] **Step 1: Delete existing migration**

```bash
rm migrations/versions/82cc9e91963b_initial_schema.py
```

- [ ] **Step 2: Delete local database**

```bash
rm -f beanbay.db
```

- [ ] **Step 3: Generate fresh initial migration**

```bash
uv run alembic revision --autogenerate -m "initial schema with evolution"
```

- [ ] **Step 4: Review the generated migration**

Open the generated file and verify:
- All new tables exist (vendors, storage_types, cuppings, bean_flavor_tags, cupping_flavor_tags)
- Bean table has new columns (roast_degree, bean_mix_type, bean_use_type, decaf, url, ean)
- Bag table has new columns (bought_at, vendor_id, frozen_at, thawed_at, storage_type_id, best_date)
- Origin has country, region; ProcessMethod has category; BeanVariety has species
- BeanOriginLink has percentage
- BrewTaste has balance, aftertaste (no aroma, intensity)
- BeanTaste has complexity, clean_cup (no bitterness, intensity)
- BeanRating has updated_at

- [ ] **Step 5: Test migration from scratch**

```bash
uv run alembic upgrade head
```

Expected: No errors

- [ ] **Step 6: Run full test suite**

```bash
uv run pytest -v
```

Expected: ALL PASS

- [ ] **Step 7: Commit**

```bash
git add migrations/versions/
git commit -m "feat: regenerate initial migration with schema evolution changes"
```

**Note:** Do NOT commit `beanbay.db`. It should be in `.gitignore`.

---

### Task 11: Full Integration Test Pass

Run the complete test suite and fix any failures.

- [ ] **Step 1: Run all tests**

```bash
uv run pytest -v --tb=short
```

- [ ] **Step 2: Fix any test failures**

Address failures one at a time. Common issues:
- Existing tests referencing removed fields (aroma, intensity, bitterness on wrong entity)
- ORM field extractors in schemas missing new fields
- Missing imports in __init__.py

- [ ] **Step 3: Run pre-commit checks**

```bash
uvx prek --all-files
```

Fix any linting/formatting issues.

- [ ] **Step 4: Final test run**

```bash
uv run pytest -v
```

Expected: ALL PASS with zero failures

- [ ] **Step 5: Commit any fixes**

```bash
git add -u
git commit -m "fix: resolve test failures from schema evolution"
```

---

## Summary of Commits

1. `feat: add BeanMixType, BeanUseType, ProcessCategory, CoffeeSpecies enums`
2. `feat: add Vendor and StorageType entities with CRUD endpoints`
3. `feat: enrich Origin, ProcessMethod, BeanVariety with structured fields`
4. `feat: enrich Bean model with roast_degree, mix_type, flavor_tags, origin percentages`
5. `feat: enrich Bag with vendor, frozen storage, bought_at, best_date`
6. `feat: rework BrewTaste axes — replace aroma/intensity with balance/aftertaste`
7. `feat: rework BeanTaste axes, add updated_at to BeanRating`
8. `feat: add Cupping entity with SCAA-protocol axes and CRUD endpoints`
9. `feat: seed storage types, update FlavorTag dependency checks`
10. `feat: regenerate initial migration with schema evolution changes`
11. `fix: resolve test failures from schema evolution` (if needed)
