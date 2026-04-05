# Bugfix Round 1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 7 bugs found during Playwright end-to-end testing of the frontend optimization UX.

**Architecture:** All 7 fixes are independent — no dependencies between them. Backend fixes use TDD. Frontend fixes verified via `bun run build`. Each task produces one commit.

**Tech Stack:** Python 3.12 / FastAPI / SQLModel (backend), React 19 / TypeScript / MUI v7 / react-plotly.js (frontend), bun (package manager)

---

## File Structure

| File | Change |
|------|--------|
| `frontend/src/components/PlotlyChart.tsx` | Fix import to factory pattern |
| `frontend/src/plotly.d.ts` | Add `react-plotly.js/factory` type declaration |
| `frontend/src/features/optimize/hooks.ts` | Fix useSuggest URL, JobStatus type, polling URL |
| `frontend/src/features/brews/components/BrewStepSetup.tsx` | Remove beans query, use `bean_name` from bag API |
| `frontend/src/features/bags/hooks.ts` | Add `bean_name` to `BagListItem` |
| `src/beanbay/schemas/bean.py` | Add `bean_name` field to `BagRead` |
| `src/beanbay/routers/beans.py` | Populate `bean_name` in bag list endpoints |
| `src/beanbay/dependencies.py` | Remove auto-resolve to default person |
| `src/beanbay/models/*.py` (8 files) | Change all datetime columns to `DateTime(timezone=True)` |
| `migrations/versions/` | Delete old migrations, generate fresh one |
| `src/beanbay/services/campaign.py` | New: `ensure_campaign()` shared helper |
| `src/beanbay/routers/brews.py` | Auto-open bag + auto-create campaign on brew creation |
| `src/beanbay/routers/optimize.py` | Refactor to use `ensure_campaign()` |
| `tests/integration/test_optimize_api.py` | Add test for auto-campaign creation |

---

### Task 1: Fix PlotlyChart — factory pattern import

**Files:**
- Modify: `frontend/src/components/PlotlyChart.tsx:1-3`
- Modify: `frontend/src/plotly.d.ts`

- [ ] **Step 1: Fix PlotlyChart import**

Replace the first 3 lines of `frontend/src/components/PlotlyChart.tsx`:

```typescript
import { useTheme } from '@mui/material';
import createPlotlyComponent from 'react-plotly.js/factory';
import Plotly from 'plotly.js-dist-min';

const Plot = createPlotlyComponent(Plotly);
```

Remove the `import type Plotly from 'plotly.js-dist-min'` line — `Plotly` is now a value import used by the factory.

- [ ] **Step 2: Update type declarations**

Replace `frontend/src/plotly.d.ts`:

```typescript
declare module 'react-plotly.js/factory' {
  import type { ComponentType } from 'react';
  import type Plotly from 'plotly.js-dist-min';

  interface PlotParams {
    data: Plotly.Data[];
    layout?: Partial<Plotly.Layout>;
    config?: Partial<Plotly.Config>;
    style?: React.CSSProperties;
    useResizeHandler?: boolean;
  }

  export default function createPlotlyComponent(
    plotly: typeof Plotly,
  ): ComponentType<PlotParams>;
}

declare module 'plotly.js-dist-min' {
  import type Plotly from 'plotly.js';
  export = Plotly;
}
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && bun run build && cd ..`

Expected: Build succeeds with no TypeScript errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/PlotlyChart.tsx frontend/src/plotly.d.ts
git commit -m "fix(frontend): use react-plotly.js factory pattern to fix ESM/CJS interop crash"
```

---

### Task 2: Fix useSuggest — correct API URL and response type

**Files:**
- Modify: `frontend/src/features/optimize/hooks.ts:185-231`

- [ ] **Step 1: Fix JobStatus interface and pollJobUntilDone URL**

In `frontend/src/features/optimize/hooks.ts`, replace the `JobStatus` interface (line ~185-189):

```typescript
interface JobStatus {
  job_id: string;
  status: string;
  result_id: string | null;
  error_message: string | null;
}
```

Fix `pollJobUntilDone` (line ~193) — the URL should include the optimize prefix:

```typescript
const { data } = await apiClient.get<JobStatus>(`/optimize/jobs/${jobId}`);
```

- [ ] **Step 2: Fix useSuggest mutation**

Replace the `useSuggest` mutation function body (lines ~205-224):

```typescript
mutationFn: async (params: SuggestParams): Promise<Recommendation> => {
  // Step 1: Create or find campaign
  const { data: campaign } = await apiClient.post('/optimize/campaigns', params);

  // Step 2: Request a recommendation
  const { data: jobRef } = await apiClient.post(
    `/optimize/campaigns/${campaign.id}/recommend`,
  );

  // Step 3: Poll job until done
  const job = await pollJobUntilDone(jobRef.job_id);
  if (job.status === 'failed' || !job.result_id) {
    throw new Error(job.error_message || 'Recommendation job failed');
  }

  // Step 4: Fetch the completed recommendation
  const { data: recommendation } = await apiClient.get<Recommendation>(
    `/optimize/recommendations/${job.result_id}`,
  );
  return recommendation;
},
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && bun run build && cd ..`

Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/optimize/hooks.ts
git commit -m "fix(frontend): correct useSuggest API URL and job status response type"
```

---

### Task 3: Fix bag autocomplete — return bean_name from API

**Files:**
- Modify: `src/beanbay/schemas/bean.py:101-149` (BagRead)
- Modify: `src/beanbay/routers/beans.py:674-755` (list_bags)
- Modify: `frontend/src/features/bags/hooks.ts`
- Modify: `frontend/src/features/brews/components/BrewStepSetup.tsx:60-122`

- [ ] **Step 1: Add bean_name to BagRead schema**

In `src/beanbay/schemas/bean.py`, add a `bean_name` field to `BagRead` (after `bean_id` at line 145):

```python
class BagRead(BagBase):
    # ... existing docstring — add bean_name to Attributes ...

    id: uuid.UUID
    bean_id: uuid.UUID
    bean_name: str | None = None  # <-- ADD THIS LINE
    created_at: datetime
    updated_at: datetime
    retired_at: datetime | None
    is_retired: bool
```

Update the `BagRead` docstring Attributes section to include:

```
    bean_name : str | None
        Name of the parent bean (denormalized for display).
```

- [ ] **Step 2: Populate bean_name in list_bags endpoint**

In `src/beanbay/routers/beans.py`, modify the `list_bags` function (line ~721). Add eager loading for the bean relationship to avoid N+1 queries, then populate `bean_name` on the serialized items. Add import at top of file:

```python
from sqlalchemy.orm import selectinload
```

In `list_bags`, add `selectinload` to the query (after `stmt = select(Bag)` at line 721):

```python
    stmt = select(Bag).options(selectinload(Bag.bean))
```

Replace the return block (lines ~748-755):

```python
    items = session.exec(stmt).all()

    return PaginatedResponse(
        items=[
            BagRead.model_validate(
                bag, update={"bean_name": bag.bean.name if bag.bean else None}
            )
            for bag in items
        ],
        total=total,
        limit=limit,
        offset=offset,
    )
```

Apply the same pattern to `list_bean_bags` (line ~546): add `.options(selectinload(Bag.bean))` to its query and use the same `model_validate(..., update={})` approach.

- [ ] **Step 3: Verify with curl**

Run: `curl -s http://localhost:8000/api/v1/bags?limit=1 | python -m json.tool | head -10`

Expected: Each bag item should include `"bean_name": "Ethiopia Yirgacheffe"` (or similar).

- [ ] **Step 4: Update frontend BagListItem type**

In `frontend/src/features/bags/hooks.ts`, add `bean_name` to `BagListItem`:

```typescript
export interface BagListItem {
  id: string; bean_id: string; bean_name: string | null; roast_date: string | null; // ... rest unchanged
```

- [ ] **Step 5: Remove beans query from BrewStepSetup and use bean_name**

In `frontend/src/features/brews/components/BrewStepSetup.tsx`:

Delete the beans query (lines 62-70):
```typescript
// DELETE THIS ENTIRE BLOCK:
const { data: beansData } = useQuery<{ items: { id: string; name: string }[] }>({
  queryKey: ['beans', { limit: 200 }],
  queryFn: async () => {
    const { data: d } = await apiClient.get('/beans', { params: { limit: 200 } });
    return d;
  },
  staleTime: 60_000,
});
```

Delete the beanMap (lines 92-93):
```typescript
// DELETE THESE LINES:
const beanMap: Record<string, string> = {};
(beansData?.items ?? []).forEach((b) => { beanMap[b.id] = b.name; });
```

In the bag `fetchFn`, update the type and label formatter (lines 104-119). Change the bag mapping to use `bean_name` from the API response:

```typescript
fetchFn={async (q) => {
  const { data: d } = await apiClient.get('/bags', { params: { q, limit: 50 } });
  const items: BagOption[] = (d.items ?? []).map(
    (bag: { id: string; bean_id: string; bean_name: string | null; weight: number | null; roast_date: string | null }) => ({
      id: bag.id,
      bean_id: bag.bean_id,
      weight: bag.weight,
      roast_date: bag.roast_date,
      name: [
        bag.bean_name ?? 'Unknown bean',
        bag.weight != null ? `${bag.weight}g` : null,
        bag.roast_date ? `roasted ${bag.roast_date}` : null,
      ]
        .filter(Boolean)
        .join(' — '),
    }),
  );
  return { items };
}}
```

Also remove the `useQuery` import if it's no longer used (check if `peopleData` query still uses it — yes it does, so keep it).

- [ ] **Step 6: Verify build**

Run: `cd frontend && bun run build && cd ..`

Expected: Build succeeds.

- [ ] **Step 7: Commit**

```bash
git add src/beanbay/schemas/bean.py src/beanbay/routers/beans.py frontend/src/features/bags/hooks.ts frontend/src/features/brews/components/BrewStepSetup.tsx
git commit -m "fix: return bean_name from bags API, remove client-side bean lookup race condition"
```

---

### Task 4: Fix dashboard stats — remove auto-resolve to default person

**Files:**
- Modify: `src/beanbay/dependencies.py:15-46`

- [ ] **Step 1: Run existing stats tests to confirm baseline**

Run: `uv run pytest tests/ -k "stats" -v --no-header`

Expected: All stats tests PASS.

- [ ] **Step 2: Modify _resolve_person_id**

In `src/beanbay/dependencies.py`, replace lines 38-46:

Before:
```python
    if person_id:
        person = session.get(Person, person_id)
        if not person or person.retired_at:
            raise HTTPException(status_code=404, detail="Person not found")
        return person_id
    default = session.exec(
        select(Person).where(Person.is_default == True)  # noqa: E712
    ).first()
    return default.id if default else None
```

After:
```python
    if person_id:
        person = session.get(Person, person_id)
        if not person or person.retired_at:
            raise HTTPException(status_code=404, detail="Person not found")
        return person_id
    return None
```

Update the docstring to reflect the change:
```python
    """Resolve an optional person_id query parameter.

    Parameters
    ----------
    session : Session
        Database session.
    person_id : uuid.UUID | None
        Explicit person ID. If ``None``, returns ``None`` (no filter).

    Returns
    -------
    uuid.UUID | None
        The validated person ID, or ``None`` for unfiltered queries.

    Raises
    ------
    HTTPException
        404 if an explicit ``person_id`` is not found or is retired.
    """
```

- [ ] **Step 3: Run stats tests again to confirm no regressions**

Run: `uv run pytest tests/ -k "stats" -v --no-header`

Expected: All stats tests still PASS.

- [ ] **Step 4: Commit**

```bash
git add src/beanbay/dependencies.py
git commit -m "fix(stats): return all-user aggregates when no person_id provided"
```

---

### Task 5: Fix timestamps — timezone-aware datetimes at the model level

This is the proper fix: make all `datetime` fields in all models timezone-aware. The app is pre-production — drop and recreate all tables.

**Files:**
- Modify: `src/beanbay/models/bean.py` — 4 `func.now()` → timezone-aware
- Modify: `src/beanbay/models/brew.py` — 6 `func.now()` → timezone-aware
- Modify: `src/beanbay/models/cupping.py` — 2 `func.now()` → timezone-aware
- Modify: `src/beanbay/models/equipment.py` — 8 `func.now()` → timezone-aware
- Modify: `src/beanbay/models/optimization.py` — 8 `func.now()` → timezone-aware
- Modify: `src/beanbay/models/person.py` — 2 `func.now()` → timezone-aware
- Modify: `src/beanbay/models/rating.py` — 5 `func.now()` → timezone-aware
- Modify: `src/beanbay/models/tag.py` — 11 `func.now()` → timezone-aware
- Modify: `migrations/` — new migration to recreate all tables with `DateTime(timezone=True)`

- [ ] **Step 1: Update all model datetime columns to timezone-aware**

In EVERY model file listed above, make two changes:

**Change A**: Add `DateTime` import and change all `sa_column_kwargs` with `func.now()` to use `DateTime(timezone=True)` column type. The pattern is:

Before:
```python
    created_at: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": func.now()},
    )
    updated_at: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()},
    )
```

After:
```python
from sqlalchemy import Column, DateTime as SADateTime

    created_at: datetime = Field(
        default=None,
        sa_column=Column(SADateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime = Field(
        default=None,
        sa_column=Column(SADateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )
```

Apply this to every `datetime` field that uses `func.now()` in all 8 model files. Also ensure `sa_type=SADateTime(timezone=True)` for any datetime fields with `index=True` (like `OptimizationJob.status`).

**Change B**: For any code that creates `datetime.now()` values in Python (e.g., in the taskiq worker), ensure they use `datetime.now(timezone.utc)`. Grep the codebase — current code already uses `datetime.now(timezone.utc)` consistently, so no Python code changes should be needed.

- [ ] **Step 2: Generate a new Alembic migration**

Since the app is pre-production, drop everything and recreate:

```bash
# Delete existing migration files
rm migrations/versions/*.py

# Generate fresh migration from current models
uv run alembic revision --autogenerate -m "initial_schema_tz_aware"
```

- [ ] **Step 3: Delete the dev database and re-run**

```bash
# Delete the SQLite database (app is pre-production, no data to preserve)
rm -f beanbay.db

# The app's lifespan handler runs alembic upgrade head on startup,
# which will create all tables fresh with timezone-aware columns.
```

- [ ] **Step 4: Run all tests to verify**

Run: `uv run pytest tests/ --no-header -q`

Expected: All tests PASS. Tests use in-memory SQLite with `SQLModel.metadata.create_all()` which picks up the new column types.

- [ ] **Step 5: Verify datetime serialization**

Start the dev server and check:
```bash
curl -s http://localhost:8000/api/v1/health
```

After creating a brew, verify:
```bash
curl -s http://localhost:8000/api/v1/brews?limit=1 | grep -o '"brewed_at":"[^"]*"'
```

Expected: `"brewed_at":"2026-03-24T11:51:49+00:00"` (with timezone offset). Pydantic serializes timezone-aware datetimes with `+00:00` suffix, which JavaScript's `new Date()` interprets as UTC.

- [ ] **Step 6: Commit**

```bash
git add src/beanbay/models/ migrations/
git commit -m "fix: use timezone-aware datetimes in all models, recreate schema"
```

---

### Task 6: Auto-create campaigns on brew creation

**Files:**
- Create: `src/beanbay/services/campaign.py`
- Modify: `src/beanbay/routers/brews.py:431-493`
- Modify: `src/beanbay/routers/optimize.py:258-324`
- Test: `tests/integration/test_optimize_api.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/integration/test_optimize_api.py`:

```python
class TestAutoCampaignOnBrew:
    """Verify campaigns are auto-created when brews are logged."""

    def test_brew_creates_campaign(self, recommend_client, recommend_session):
        """Creating a brew auto-creates a campaign for the bean+setup."""
        seed_brew_methods(recommend_session)
        recommend_session.commit()
        seed_method_parameter_defaults(recommend_session)
        recommend_session.commit()

        method_id = _create_brew_method(recommend_client, "espresso_auto1")
        bean_id = _create_bean(recommend_client, "Auto Bean")
        setup_id = _create_brew_setup(recommend_client, method_id)
        person_id = _create_person(recommend_client, "Auto Tester")
        bag_id = _create_bag(recommend_client, bean_id)

        # Before brew: no campaign should exist
        resp = recommend_client.get(
            CAMPAIGNS, params={"bean_id": bean_id}
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 0

        # Create a brew
        _create_brew_with_taste(
            recommend_client, bag_id, setup_id, person_id, score=7.5,
        )

        # After brew: campaign should exist
        resp = recommend_client.get(
            CAMPAIGNS, params={"bean_id": bean_id}
        )
        assert resp.status_code == 200
        campaigns = resp.json()
        assert len(campaigns) >= 1
        campaign = campaigns[0]
        assert campaign["bean_name"] is not None
        assert campaign["brew_setup_name"] is not None

    def test_second_brew_same_campaign(self, recommend_client, recommend_session):
        """A second brew for the same bean+setup does not create a second campaign."""
        seed_brew_methods(recommend_session)
        recommend_session.commit()
        seed_method_parameter_defaults(recommend_session)
        recommend_session.commit()

        method_id = _create_brew_method(recommend_client, "espresso_auto2")
        bean_id = _create_bean(recommend_client, "Auto Bean 2")
        setup_id = _create_brew_setup(recommend_client, method_id)
        person_id = _create_person(recommend_client, "Auto Tester 2")
        bag_id = _create_bag(recommend_client, bean_id)

        _create_brew_with_taste(
            recommend_client, bag_id, setup_id, person_id, score=7.0,
        )
        _create_brew_with_taste(
            recommend_client, bag_id, setup_id, person_id, score=8.0,
        )

        resp = recommend_client.get(
            CAMPAIGNS, params={"bean_id": bean_id}
        )
        campaigns = resp.json()
        matching = [c for c in campaigns if c["brew_setup_name"] is not None]
        assert len(matching) == 1  # Only one campaign, not two
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/integration/test_optimize_api.py::TestAutoCampaignOnBrew -v --no-header -x`

Expected: FAIL (no campaign exists after brew creation).

- [ ] **Step 3: Create ensure_campaign service**

Create `src/beanbay/services/campaign.py`:

```python
"""Shared campaign creation logic."""

from __future__ import annotations

import uuid

from sqlmodel import Session, select

from beanbay.models.optimization import Campaign


def ensure_campaign(
    session: Session,
    *,
    bean_id: uuid.UUID,
    brew_setup_id: uuid.UUID,
) -> tuple[Campaign, bool]:
    """Return existing campaign or create a new one for the bean+setup pair.

    Idempotent: if a campaign already exists for this combination,
    returns it without modification. Otherwise creates a new campaign
    with default state.

    Parameters
    ----------
    session : Session
        Database session.
    bean_id : uuid.UUID
        Bean foreign key.
    brew_setup_id : uuid.UUID
        Brew setup foreign key.

    Returns
    -------
    tuple[Campaign, bool]
        The campaign and whether it was newly created (True) or
        already existed (False).
    """
    existing = session.exec(
        select(Campaign).where(
            Campaign.bean_id == bean_id,
            Campaign.brew_setup_id == brew_setup_id,
        )
    ).first()

    if existing is not None:
        return existing, False

    campaign = Campaign(bean_id=bean_id, brew_setup_id=brew_setup_id)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign, True
```

- [ ] **Step 4: Call ensure_campaign from create_brew**

In `src/beanbay/routers/brews.py`, add import at top:

```python
from beanbay.services.campaign import ensure_campaign
```

In `create_brew()`, add after `session.commit()` (line 491) and before `session.refresh(db_brew)`:

```python
    session.commit()

    # Auto-create campaign for this bean+setup combination
    ensure_campaign(
        session, bean_id=bag.bean_id, brew_setup_id=payload.brew_setup_id
    )  # return value not needed here

    session.refresh(db_brew)
```

- [ ] **Step 5: Refactor optimize router to use ensure_campaign**

In `src/beanbay/routers/optimize.py`, add import:

```python
from beanbay.services.campaign import ensure_campaign
```

In `create_or_get_campaign()` (line ~293-324), keep the FK validation (bean/setup 404 checks) but replace the campaign lookup+creation block with `ensure_campaign`. The function returns `(campaign, created)`:

```python
    # Validate bean_id
    bean = session.get(Bean, payload.bean_id)
    if bean is None:
        raise HTTPException(status_code=404, detail="Bean not found.")

    # Validate brew_setup_id
    setup = session.get(BrewSetup, payload.brew_setup_id)
    if setup is None:
        raise HTTPException(status_code=404, detail="BrewSetup not found.")

    campaign, created = ensure_campaign(
        session, bean_id=payload.bean_id, brew_setup_id=payload.brew_setup_id
    )

    if not created:
        response.status_code = 200

    return _campaign_to_detail(session, campaign)
```

This preserves the 201/200 distinction and FK validation, matching existing test expectations.

- [ ] **Step 6: Run tests**

Run: `uv run pytest tests/integration/test_optimize_api.py -v --no-header`

Expected: All tests PASS including the two new ones.

- [ ] **Step 7: Commit**

```bash
git add src/beanbay/services/campaign.py src/beanbay/routers/brews.py src/beanbay/routers/optimize.py tests/integration/test_optimize_api.py
git commit -m "feat: auto-create optimization campaign when brew is logged"
```

---

### Task 7: Auto-set bag opened_at on brew creation

**Files:**
- Modify: `src/beanbay/routers/brews.py:438-484`

- [ ] **Step 1: Add bag auto-open logic to create_brew**

In `src/beanbay/routers/brews.py`, add import at module top (if not already present):

```python
from datetime import datetime, timezone
```

In the `create_brew()` function, add after the bag validation (after line 440) and before the grind setting resolution:

```python
    bag = session.get(Bag, payload.bag_id)
    if bag is None:
        raise HTTPException(status_code=404, detail="Bag not found.")

    # Auto-mark bag as opened when first used in a brew
    if bag.opened_at is None:
        bag.opened_at = datetime.now(timezone.utc)
        session.add(bag)
```

Note: `opened_at` is a `datetime` field on the Bag model, so we use `datetime.now(timezone.utc)` (not `date.today()`).

- [ ] **Step 2: Verify with existing tests**

Run: `uv run pytest tests/ --no-header -q`

Expected: All tests PASS.

- [ ] **Step 3: Commit**

```bash
git add src/beanbay/routers/brews.py
git commit -m "fix: auto-set bag opened_at when first used in a brew"
```

---

## Final Verification

After all tasks:

- [ ] **Backend tests**: `uv run pytest tests/ --no-header -q` — all pass
- [ ] **Frontend build**: `cd frontend && bun run build && cd ..` — clean build
- [ ] **Manual smoke test**: Open `http://localhost:5173/`, verify:
  - Brew detail page renders TasteRadar chart (not blank)
  - Campaign detail page renders all 8 charts
  - Person preferences page renders charts
  - Suggest button works in BrewWizard step 1
  - Bag autocomplete shows bean names
  - Dashboard stats show non-zero values
  - "Recent Brews" shows correct relative times
  - Optimize page shows campaigns
  - "Bags Unopened" count decreases for used bags
