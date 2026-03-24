# Personalized Taste Insights & Hybrid Optimization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add off-by-default sub-score sliders, per-person taste profile insights, and hybrid community/personal optimization.

**Architecture:** Three independent features sharing a common theme. (1) Frontend slider UX change with no backend impact. (2) Backend taste profile computation added to the existing preferences endpoint, displayed via existing TasteRadar component. (3) person_id + mode threading from the suggest flow through the async job pipeline to the broker's measurement query, with a toggle badge on the frontend.

**Tech Stack:** FastAPI, SQLModel/SQLite, taskiq, React, MUI, Plotly (TasteRadar), TanStack Query

**Spec:** `docs/superpowers/specs/2026-03-24-personalized-taste-insights-design.md`

---

## File Structure

### Backend — Models
- **Modify:** `src/beanbay/models/optimization.py` — add 2 columns to `OptimizationJob`, 2 columns to `Recommendation`

### Backend — Schemas
- **Modify:** `src/beanbay/schemas/optimization.py` — add `TasteProfile` schema, extend `PersonPreferences`, extend `RecommendationRead`, add `RecommendRequest` body schema

### Backend — Endpoints
- **Modify:** `src/beanbay/routers/optimize.py` — compute taste profile in `get_person_preferences`; accept JSON body on `request_recommendation`

### Backend — Broker
- **Modify:** `src/beanbay/services/taskiq_broker.py` — read person_id/mode from job, filter measurements, set mode metadata on recommendation

### Frontend — Slider UX
- **Modify:** `frontend/src/features/brews/components/BrewStepTaste.tsx` — off-by-default sliders with X reset
- **Modify:** `frontend/src/features/brews/pages/BrewDetailPage.tsx` — same pattern in TasteFormDialog

### Frontend — Taste Profile
- **Modify:** `frontend/src/features/people/pages/PersonPreferencesPage.tsx` — new section
- **Modify:** `frontend/src/features/optimize/hooks.ts` — extend `PersonPreferences` type

### Frontend — Hybrid Optimization
- **Modify:** `frontend/src/features/optimize/hooks.ts` — extend `useSuggest`, `SuggestParams`, `Recommendation` types
- **Modify:** `frontend/src/features/optimize/components/SuggestButton.tsx` — accept `personId`
- **Modify:** `frontend/src/features/brews/components/BrewWizard.tsx` — pass person to SuggestButton
- **Modify:** `frontend/src/features/optimize/pages/CampaignDetailPage.tsx` — toggle badge

### Tests
- **Modify:** `tests/integration/test_optimize_api.py` — taste profile tests, hybrid optimization tests

---

## Task 1: Add model columns for person-aware optimization

**Files:**
- Modify: `src/beanbay/models/optimization.py:248-286` (OptimizationJob) and `:198-241` (Recommendation)

- [ ] **Step 1: Write failing test — OptimizationJob has person_id and optimization_mode columns**

In `tests/integration/test_optimize_api.py`, add at the end:

```python
class TestPersonAwareOptimization:
    """OptimizationJob and Recommendation support person-aware fields."""

    def test_optimization_job_has_person_fields(self, session):
        """OptimizationJob model has person_id and optimization_mode columns."""
        from beanbay.models.optimization import OptimizationJob
        job = OptimizationJob(
            campaign_id=uuid.uuid4(),
            job_type="recommend",
            person_id=uuid.uuid4(),
            optimization_mode="personal",
        )
        session.add(job)
        session.flush()
        session.refresh(job)
        assert job.person_id is not None
        assert job.optimization_mode == "personal"

    def test_recommendation_has_mode_fields(self, session):
        """Recommendation model has optimization_mode and personal_brew_count."""
        from beanbay.models.optimization import Recommendation
        rec = Recommendation(
            campaign_id=uuid.uuid4(),
            phase="random",
            parameter_values="{}",
            optimization_mode="community",
            personal_brew_count=3,
        )
        session.add(rec)
        session.flush()
        session.refresh(rec)
        assert rec.optimization_mode == "community"
        assert rec.personal_brew_count == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_optimize_api.py::TestPersonAwareOptimization -v`
Expected: FAIL — `unexpected keyword argument 'person_id'`

- [ ] **Step 3: Add columns to models**

In `src/beanbay/models/optimization.py`, add to `OptimizationJob` class (after `completed_at` field around line 285):

```python
    person_id: uuid.UUID | None = Field(default=None, description="Person for personalized mode")
    optimization_mode: str | None = Field(default=None, description="community or personal")
```

Add to `Recommendation` class (after `status` field around line 235):

```python
    optimization_mode: str | None = Field(default=None, description="community or personal")
    personal_brew_count: int | None = Field(default=None, description="Person's brew count when generated")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/integration/test_optimize_api.py::TestPersonAwareOptimization -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add src/beanbay/models/optimization.py tests/integration/test_optimize_api.py
git commit -m "feat(models): add person_id and optimization_mode to OptimizationJob and Recommendation"
```

---

## Task 2: Extend schemas for person-aware recommendations

**Files:**
- Modify: `src/beanbay/schemas/optimization.py:158-232` (RecommendationRead) and `:512-540` (PersonPreferences)

- [ ] **Step 1: Write failing test — RecommendationRead includes new fields**

```python
class TestRecommendationReadSchema:
    """RecommendationRead schema includes optimization_mode fields."""

    def test_recommendation_read_has_mode_fields(self, recommend_client, recommend_session):
        """RecommendationRead exposes optimization_mode and personal_brew_count."""
        ids = _setup_campaign(recommend_client, recommend_session)
        resp = recommend_client.post(RECOMMEND.format(campaign_id=ids["campaign_id"]))
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]
        job_resp = recommend_client.get(f"{JOBS}/{job_id}")
        assert job_resp.json()["status"] == "completed"
        result_id = job_resp.json()["result_id"]

        rec_resp = recommend_client.get(f"{RECOMMENDATIONS}/{result_id}")
        rec = rec_resp.json()
        # Fields should exist (null is fine for legacy recommendations)
        assert "optimization_mode" in rec
        assert "personal_brew_count" in rec
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_optimize_api.py::TestRecommendationReadSchema -v`
Expected: FAIL — `'optimization_mode' not in rec`

- [ ] **Step 3: Add fields to schemas**

In `src/beanbay/schemas/optimization.py`, add to `RecommendationRead` (after `created_at` line ~191):

```python
    optimization_mode: str | None = None
    personal_brew_count: int | None = None
```

Also add the `parse_parameter_values` validator's field list needs updating — add `"optimization_mode"` and `"personal_brew_count"` to the `for field in (...)` tuple around line 212.

Add new schema for the recommend request body (after `RecommendationRead`):

```python
class RecommendRequest(SQLModel):
    """Optional body for POST /campaigns/{id}/recommend."""

    person_id: uuid.UUID | None = None
    mode: str = "auto"
```

Add taste profile schema and extend PersonPreferences (before `PersonPreferences` class):

```python
class TasteProfile(SQLModel):
    """Averaged sub-scores from a person's top brews."""

    acidity: float | None = None
    sweetness: float | None = None
    body: float | None = None
    bitterness: float | None = None
    balance: float | None = None
    aftertaste: float | None = None
```

Add to `PersonPreferences` (after `method_breakdown` line ~539):

```python
    taste_profile: TasteProfile | None = None
    taste_profile_brew_count: int = 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/integration/test_optimize_api.py::TestRecommendationReadSchema -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/beanbay/schemas/optimization.py tests/integration/test_optimize_api.py
git commit -m "feat(schemas): add RecommendRequest, TasteProfile, and mode fields to RecommendationRead"
```

---

## Task 3: Taste profile computation in preferences endpoint

**Files:**
- Modify: `src/beanbay/routers/optimize.py` — the `get_person_preferences` endpoint (around line 1241)

- [ ] **Step 1: Write failing test — preferences returns taste_profile**

```python
class TestTasteProfile:
    """GET /optimize/people/{id}/preferences returns taste_profile."""

    def test_taste_profile_from_top_brews(self, client, session):
        """Taste profile averages sub-scores from top-5 brews by score."""
        ids = _setup_campaign_with_scored_brews(client, session, n_brews=5)
        person_id = ids["person_id"]

        # Add sub-scores to each brew's taste
        for i, brew_id in enumerate(ids["brew_ids"]):
            client.patch(
                f"/api/v1/brews/{brew_id}/taste",
                json={
                    "acidity": 5.0 + i,
                    "sweetness": 6.0 + i,
                    "body": 7.0,
                },
            )

        resp = client.get(f"/api/v1/optimize/people/{person_id}/preferences")
        assert resp.status_code == 200
        data = resp.json()
        assert data["taste_profile"] is not None
        assert data["taste_profile_brew_count"] >= 3
        # acidity should be averaged from top brews
        assert data["taste_profile"]["acidity"] is not None
        assert data["taste_profile"]["sweetness"] is not None
        assert data["taste_profile"]["body"] is not None

    def test_taste_profile_null_when_insufficient_data(self, client, session):
        """Taste profile is null when fewer than 3 qualifying brews."""
        from beanbay.seed import seed_brew_methods
        from beanbay.seed_optimization import seed_method_parameter_defaults

        seed_brew_methods(session)
        session.commit()
        seed_method_parameter_defaults(session)
        session.commit()

        # Create a person with no brews
        resp = client.post("/api/v1/people", json={"name": "No Brews Person"})
        person_id = resp.json()["id"]

        resp = client.get(f"/api/v1/optimize/people/{person_id}/preferences")
        assert resp.status_code == 200
        data = resp.json()
        assert data["taste_profile"] is None
        assert data["taste_profile_brew_count"] == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_optimize_api.py::TestTasteProfile -v`
Expected: FAIL — `'taste_profile' not in data` or `KeyError`

- [ ] **Step 3: Implement taste profile computation**

In `src/beanbay/routers/optimize.py`, in the `get_person_preferences` function (around line 1241), add taste profile computation before the return statement. Import `TasteProfile` from schemas.

```python
from beanbay.schemas.optimization import TasteProfile

# --- Taste profile: average sub-scores from top-5 brews ---
SUB_SCORE_AXES = ["acidity", "sweetness", "body", "bitterness", "balance", "aftertaste"]

taste_brews = session.exec(
    select(Brew)
    .join(Bag, Brew.bag_id == Bag.id)
    .join(BrewTaste, Brew.id == BrewTaste.brew_id)
    .where(
        Brew.person_id == person_id,
        Brew.is_failed == False,  # noqa: E712
        Brew.retired_at.is_(None),  # type: ignore[union-attr]
        BrewTaste.score.is_not(None),  # type: ignore[union-attr]
    )
    .order_by(BrewTaste.score.desc(), Brew.brewed_at.desc())  # type: ignore[union-attr]
).all()

# Filter to brews with >= 3 non-null sub-scores
qualifying = []
for brew in taste_brews:
    taste = brew.taste
    if taste is None:
        continue
    non_null_count = sum(1 for ax in SUB_SCORE_AXES if getattr(taste, ax) is not None)
    if non_null_count >= 3:
        qualifying.append(taste)
    if len(qualifying) == 5:
        break

taste_profile = None
taste_profile_brew_count = len(qualifying)

if len(qualifying) >= 3:
    profile_values = {}
    for ax in SUB_SCORE_AXES:
        values = [getattr(t, ax) for t in qualifying if getattr(t, ax) is not None]
        profile_values[ax] = round(sum(values) / len(values), 1) if len(values) >= 2 else None
    taste_profile = TasteProfile(**profile_values)
```

Add `taste_profile=taste_profile, taste_profile_brew_count=taste_profile_brew_count` to the `PersonPreferences` return.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/integration/test_optimize_api.py::TestTasteProfile -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add src/beanbay/routers/optimize.py tests/integration/test_optimize_api.py
git commit -m "feat(preferences): compute taste profile from top-5 brews"
```

---

## Task 4: Hybrid optimization — recommend endpoint accepts person_id and mode

**Files:**
- Modify: `src/beanbay/routers/optimize.py:989-1036` (request_recommendation endpoint)

- [ ] **Step 1: Write failing test — recommend accepts person_id and mode**

```python
class TestHybridOptimization:
    """POST /campaigns/{id}/recommend supports person_id and mode."""

    def test_recommend_accepts_person_id(self, recommend_client, recommend_session):
        """Recommend endpoint accepts person_id in body and stores on job."""
        ids = _setup_campaign_with_scored_brews(
            recommend_client, recommend_session, n_brews=5,
        )
        resp = recommend_client.post(
            RECOMMEND.format(campaign_id=ids["campaign_id"]),
            json={"person_id": ids["person_id"], "mode": "personal"},
        )
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]

        job_resp = recommend_client.get(f"{JOBS}/{job_id}")
        assert job_resp.json()["status"] == "completed"
        result_id = job_resp.json()["result_id"]

        rec_resp = recommend_client.get(f"{RECOMMENDATIONS}/{result_id}")
        rec = rec_resp.json()
        assert rec["optimization_mode"] == "personal"
        assert rec["personal_brew_count"] == 5

    def test_recommend_without_person_uses_community(
        self, recommend_client, recommend_session,
    ):
        """Recommend without person_id defaults to community mode."""
        ids = _setup_campaign(recommend_client, recommend_session)
        resp = recommend_client.post(
            RECOMMEND.format(campaign_id=ids["campaign_id"]),
        )
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]

        job_resp = recommend_client.get(f"{JOBS}/{job_id}")
        assert job_resp.json()["status"] == "completed"
        result_id = job_resp.json()["result_id"]

        rec_resp = recommend_client.get(f"{RECOMMENDATIONS}/{result_id}")
        rec = rec_resp.json()
        assert rec["optimization_mode"] == "community"

    def test_auto_mode_graduates_to_personal(
        self, recommend_client, recommend_session,
    ):
        """Auto mode resolves to personal when person has >= 5 brews."""
        ids = _setup_campaign_with_scored_brews(
            recommend_client, recommend_session, n_brews=5,
        )
        resp = recommend_client.post(
            RECOMMEND.format(campaign_id=ids["campaign_id"]),
            json={"person_id": ids["person_id"], "mode": "auto"},
        )
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]
        job_resp = recommend_client.get(f"{JOBS}/{job_id}")
        assert job_resp.json()["status"] == "completed"
        result_id = job_resp.json()["result_id"]

        rec_resp = recommend_client.get(f"{RECOMMENDATIONS}/{result_id}")
        rec = rec_resp.json()
        assert rec["optimization_mode"] == "personal"
        assert rec["personal_brew_count"] == 5

    def test_personal_mode_no_brews_returns_error(
        self, recommend_client, recommend_session,
    ):
        """Personal mode with 0 brews for this person fails gracefully."""
        ids = _setup_campaign(recommend_client, recommend_session)
        # Create a different person with no brews
        resp = recommend_client.post("/api/v1/people", json={"name": "No Brews"})
        other_person_id = resp.json()["id"]

        resp = recommend_client.post(
            RECOMMEND.format(campaign_id=ids["campaign_id"]),
            json={"person_id": other_person_id, "mode": "personal"},
        )
        # Job should complete but recommendation should fail or have 0 measurements
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]
        job_resp = recommend_client.get(f"{JOBS}/{job_id}")
        job = job_resp.json()
        # Either the job fails with an error message, or completes with 0 personal brews
        assert job["status"] in ("completed", "failed")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_optimize_api.py::TestHybridOptimization -v`
Expected: FAIL — endpoint doesn't read body, `optimization_mode` is null

- [ ] **Step 3: Update recommend endpoint to accept body and store on job**

In `src/beanbay/routers/optimize.py`, modify `request_recommendation` (line ~989):

```python
from beanbay.schemas.optimization import RecommendRequest

async def request_recommendation(
    campaign_id: uuid.UUID,
    session: SessionDep,
    body: RecommendRequest | None = None,
) -> dict:
    # ... existing campaign lookup ...

    person_id = body.person_id if body else None
    mode = body.mode if body else "auto"

    job = OptimizationJob(
        campaign_id=campaign.id,
        job_type="recommend",
        person_id=person_id,
        optimization_mode=mode,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    await generate_recommendation.kiq(str(job.id))
    return {"job_id": str(job.id), "status": "pending"}
```

- [ ] **Step 4: Update broker to read person_id/mode and filter measurements**

In `src/beanbay/services/taskiq_broker.py`, in `generate_recommendation`, after loading the campaign (around line 57), read person context from the job:

```python
            person_id = job.person_id
            requested_mode = job.optimization_mode or "auto"
```

Before the measurement query (around line 109), resolve the mode and build the query:

```python
            # Resolve optimization mode
            if requested_mode == "auto" and person_id is not None:
                # Count this person's scored brews for this bean+setup
                personal_count_stmt = (
                    select(func.count())
                    .select_from(Brew)
                    .join(Bag, Brew.bag_id == Bag.id)
                    .join(BrewTaste, Brew.id == BrewTaste.brew_id)
                    .where(
                        Bag.bean_id == campaign_row.bean_id,
                        Brew.brew_setup_id == campaign_row.brew_setup_id,
                        Brew.person_id == person_id,
                        Brew.is_failed == False,  # noqa: E712
                        Brew.retired_at.is_(None),
                        BrewTaste.score.is_not(None),
                    )
                )
                personal_count = session.exec(personal_count_stmt).one()
                resolved_mode = "personal" if personal_count >= 5 else "community"
            elif requested_mode == "personal":
                resolved_mode = "personal"
            else:
                resolved_mode = "community"
```

Then modify the existing measurement query to add person filter when personal:

```python
            stmt = (
                select(Brew)
                .join(Bag, Brew.bag_id == Bag.id)
                .join(BrewTaste, Brew.id == BrewTaste.brew_id)
                .where(
                    Bag.bean_id == campaign_row.bean_id,
                    Brew.brew_setup_id == campaign_row.brew_setup_id,
                    Brew.is_failed == False,
                    Brew.retired_at.is_(None),
                    BrewTaste.score.is_not(None),
                )
            )
            if resolved_mode == "personal" and person_id is not None:
                stmt = stmt.where(Brew.person_id == person_id)
            brews = session.exec(stmt).all()
```

After creating the Recommendation row (around line 168), set the metadata:

```python
            rec.optimization_mode = resolved_mode
            if resolved_mode == "personal" and person_id is not None:
                rec.personal_brew_count = len(brews)
            else:
                rec.personal_brew_count = None
```

Import `func` from sqlalchemy if not already imported.

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/integration/test_optimize_api.py::TestHybridOptimization -v`
Expected: PASS

- [ ] **Step 6: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All pass

- [ ] **Step 7: Commit**

```bash
git add src/beanbay/routers/optimize.py src/beanbay/services/taskiq_broker.py tests/integration/test_optimize_api.py
git commit -m "feat(optimization): hybrid community/personal recommendation with person_id threading"
```

---

## Task 5: Off-by-default sub-score sliders — BrewStepTaste

**Files:**
- Modify: `frontend/src/features/brews/components/BrewStepTaste.tsx`
- Modify: `frontend/src/features/brews/components/BrewWizard.tsx` (TasteData type, initial state)

- [ ] **Step 1: Update BrewWizard initialState**

Note: `BrewStepTaste.tsx` already accepts `number | null` for sub-score props. Only the BrewWizard's `initialState` (line ~60) needs updating — change sub-score defaults from `0` to `null`:

```typescript
taste: {
  score: 0,
  acidity: null,
  sweetness: null,
  body: null,
  bitterness: null,
  balance: null,
  aftertaste: null,
  notes: '',
  flavor_tags: [],
},
```

- [ ] **Step 2: Update TasteSlider in BrewStepTaste to render off-by-default**

In `BrewStepTaste.tsx`, modify the `TasteSlider` sub-component (lines ~34-64) to handle null state:

```tsx
function TasteSlider({ label, value, onChange }: {
  label: string; value: number | null; onChange: (v: number | null) => void;
}) {
  const isOff = value === null;
  return (
    <Box sx={{ px: 1 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="body2" color={isOff ? 'text.disabled' : 'text.primary'}>
          {label}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Typography variant="body2" color={isOff ? 'text.disabled' : 'text.primary'}>
            {isOff ? '—' : value.toFixed(1)}
          </Typography>
          {!isOff && (
            <IconButton size="small" onClick={() => onChange(null)} sx={{ p: 0.25 }}>
              <CloseIcon sx={{ fontSize: 14 }} />
            </IconButton>
          )}
        </Box>
      </Box>
      <Slider
        value={value ?? 5}
        onChange={(_, v) => onChange(v as number)}
        min={0} max={10} step={0.5}
        valueLabelDisplay="auto"
        sx={{ opacity: isOff ? 0.3 : 1 }}
      />
      {isOff && (
        <Typography variant="caption" color="text.disabled" sx={{ mt: -1, display: 'block' }}>
          Tap to rate
        </Typography>
      )}
    </Box>
  );
}
```

Import `CloseIcon` from `@mui/icons-material/Close` and `IconButton` from `@mui/material`.
Overall score slider stays always-on (no null state, no X button).

- [ ] **Step 3: Update buildBody in BrewWizard to send null for off sliders**

In the `handleSubmit` / `buildBody` section of `BrewWizard.tsx`, ensure sub-scores that are `null` are sent as `null` (or omitted) in the taste payload, not as `0`.

- [ ] **Step 4: Build and verify**

Run: `cd frontend && bun run build`
Expected: Build succeeds

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/brews/components/BrewStepTaste.tsx frontend/src/features/brews/components/BrewWizard.tsx
git commit -m "feat(frontend): off-by-default sub-score sliders with tap-to-engage and X reset"
```

---

## Task 6: Off-by-default sliders in TasteFormDialog

**Files:**
- Modify: `frontend/src/features/brews/pages/BrewDetailPage.tsx:179-277`

- [ ] **Step 1: Update TasteFormState type**

Change sub-score fields from `number` to `number | null`.

- [ ] **Step 2: Update defaultTasteForm**

For new taste (no existing): sub-scores default to `null`.
For existing taste: use stored values (null stays null, numbers stay engaged).

```typescript
function defaultTasteForm(taste?: BrewTaste | null): TasteFormState {
  return {
    score: taste?.score ?? 7,
    acidity: taste?.acidity ?? null,
    sweetness: taste?.sweetness ?? null,
    body: taste?.body ?? null,
    bitterness: taste?.bitterness ?? null,
    balance: taste?.balance ?? null,
    aftertaste: taste?.aftertaste ?? null,
    notes: taste?.notes ?? '',
    flavor_tags: taste?.flavor_tags ?? [],
  };
}
```

- [ ] **Step 3: Apply same slider pattern as BrewStepTaste**

Use the same off-by-default slider pattern from Task 5 in the dialog's slider rendering.

- [ ] **Step 4: Update submit handler to send null for off sliders**

Ensure the PUT/PATCH call sends `null` for sub-scores that are off.

- [ ] **Step 5: Build and verify**

Run: `cd frontend && bun run build`
Expected: Build succeeds

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/brews/pages/BrewDetailPage.tsx
git commit -m "feat(frontend): off-by-default sliders in taste edit dialog"
```

---

## Task 7: Taste Profile section on Person Preferences page

**Files:**
- Modify: `frontend/src/features/optimize/hooks.ts` — extend PersonPreferences type
- Modify: `frontend/src/features/people/pages/PersonPreferencesPage.tsx` — add section

- [ ] **Step 1: Extend PersonPreferences type in hooks.ts**

Add to the `PersonPreferences` interface:

```typescript
taste_profile: {
  acidity: number | null;
  sweetness: number | null;
  body: number | null;
  bitterness: number | null;
  balance: number | null;
  aftertaste: number | null;
} | null;
taste_profile_brew_count: number;
```

- [ ] **Step 2: Add Taste Profile section to PersonPreferencesPage**

After the Top Beans section, add:

```tsx
{data.taste_profile && (
  <Grid size={{ xs: 12, md: 6 }}>
    <Section title="Taste Profile">
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Based on your {data.taste_profile_brew_count} best brews
      </Typography>
      <TasteRadar data={profileToRadar(data.taste_profile)} size={300} />
    </Section>
  </Grid>
)}
```

Create a `profileToRadar` helper that converts the taste_profile object to `TasteDataPoint[]` using `?? 0` for null axes.

- [ ] **Step 3: Build and verify**

Run: `cd frontend && bun run build`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/optimize/hooks.ts frontend/src/features/people/pages/PersonPreferencesPage.tsx
git commit -m "feat(frontend): taste profile radar on person preferences page"
```

---

## Task 8: Frontend suggest flow — pass person_id and mode

**Files:**
- Modify: `frontend/src/features/optimize/hooks.ts:180-232`
- Modify: `frontend/src/features/optimize/components/SuggestButton.tsx`
- Modify: `frontend/src/features/brews/components/BrewWizard.tsx`

- [ ] **Step 1: Extend SuggestParams and useSuggest**

In `hooks.ts`, add `person_id` and `mode` to `SuggestParams`:

```typescript
interface SuggestParams {
  bean_id: string;
  brew_setup_id: string;
  person_id?: string;
  mode?: string;
}
```

In `useSuggest`, pass `person_id` and `mode` to the recommend step (step 2):

```typescript
const { data: jobRef } = await apiClient.post(
  `/optimize/campaigns/${campaign.id}/recommend`,
  { person_id: params.person_id, mode: params.mode },
);
```

Extend the `Recommendation` interface:

```typescript
optimization_mode: string | null;
personal_brew_count: number | null;
```

- [ ] **Step 2: Update SuggestButton to accept and pass personId**

Add `personId?: string` to SuggestButton Props. Pass it through to `suggest.mutateAsync`:

```typescript
const rec = await suggest.mutateAsync({
  bean_id: beanId,
  brew_setup_id: brewSetupId,
  person_id: personId,
});
```

- [ ] **Step 3: Update BrewWizard to pass person to SuggestButton**

In `BrewWizard.tsx`, where `SuggestButton` is rendered, add `personId={state.setup.person?.id}`.

- [ ] **Step 4: Build and verify**

Run: `cd frontend && bun run build`
Expected: Build succeeds

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/optimize/hooks.ts frontend/src/features/optimize/components/SuggestButton.tsx frontend/src/features/brews/components/BrewWizard.tsx
git commit -m "feat(frontend): pass person_id through suggest flow for hybrid optimization"
```

---

## Task 9: Community/Personal toggle badge on campaign detail

**Files:**
- Modify: `frontend/src/features/optimize/pages/CampaignDetailPage.tsx`

- [ ] **Step 1: Add toggle badge to stats header**

Read the most recent recommendation's `optimization_mode` from the recommendations list. Track user override in state (synced to localStorage). Show a clickable Chip:

```tsx
const latestRec = recommendations?.[recommendations.length - 1];
const storageKey = `beanbay:opt-mode:${campaignId}`;
const [userOverride, setUserOverride] = useState<string | null>(
  () => localStorage.getItem(storageKey)
);

const resolvedMode = userOverride ?? latestRec?.optimization_mode ?? 'community';
const isForced = userOverride != null;
const brewCount = latestRec?.personal_brew_count;

// Chip label per spec: "Community (3 brews)", "Personal (7 brews)", "Community (forced)"
const chipLabel = isForced
  ? `${resolvedMode === 'personal' ? 'Personal' : 'Community'} (forced)`
  : `${resolvedMode === 'personal' ? 'Personal' : 'Community'}${brewCount != null ? ` (${brewCount} brews)` : ''}`;

<Chip
  label={chipLabel}
  color={resolvedMode === 'personal' ? 'success' : 'default'}
  onClick={() => {
    const next = resolvedMode === 'personal' ? 'community' : 'personal';
    localStorage.setItem(storageKey, next);
    setUserOverride(next);
  }}
  clickable
  size="small"
/>
```

Place this chip in the stats header Grid, e.g. after the Convergence card.

Also add the `useCampaignRecommendations` hook call to get `recommendations` data for the badge. Import it alongside existing hooks.

- [ ] **Step 2: Build and verify**

Run: `cd frontend && bun run build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/optimize/pages/CampaignDetailPage.tsx
git commit -m "feat(frontend): clickable community/personal optimization badge"
```

---

## Task 10: End-to-end verification

- [ ] **Step 1: Run full backend test suite**

Run: `uv run pytest tests/ -v`
Expected: All pass

- [ ] **Step 2: Run frontend build**

Run: `cd frontend && bun run build`
Expected: Build succeeds with no errors

- [ ] **Step 3: Manual smoke test**

1. Open `/brews/new`, go to taste step — sub-score sliders should be grayed/off, tap to engage, X to reset
2. Open `/people/{id}/preferences` — should show Taste Profile radar if enough rated brews
3. Open `/brews/new`, select bag + setup + person, click "Get Suggestion" — suggestion should show community/personal badge
4. Open `/optimize/{campaignId}` — stats header should show community/personal chip, clickable to toggle
