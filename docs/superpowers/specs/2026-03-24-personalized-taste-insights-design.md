# Personalized Taste Insights & Hybrid Optimization

**Date:** 2026-03-24
**Status:** Draft

## Problem

1. Sub-score sliders (acidity, sweetness, body, bitterness, balance, aftertaste) have no null/unrated state — 0 is indistinguishable from "didn't rate." Users can't reset an accidentally touched slider.
2. Sub-score data is collected but never used — no insights, no impact on optimization.
3. Optimization campaigns are person-agnostic. Two people with different palates get the same suggestion, converging on a mediocre middle ground.

## Design

### 1. Sub-Score Slider UX: "Off by Default"

Sliders start in a disabled/grayed-out "off" state. The user must actively tap or click to engage a slider. An X icon clears it back to off. Only engaged sliders send values to the API; off sliders send `null`.

**Behavior:**
- Initial state: all sub-score sliders are off (overall score slider remains always-on at 5.0)
- Tap/click on the slider track or thumb engages it at that position
- Small X icon appears next to engaged sliders — clicking it resets to off
- Off sliders render as grayed/muted with a "tap to rate" hint
- Submitting with off sliders sends `null` for those fields (no change to API schema — fields are already nullable)

**Applies to both:**
- **Brew wizard taste step** (`BrewStepTaste`): `TasteData` type changes sub-score fields from `number` to `number | null`, initial state is `null` for all sub-scores
- **Brew detail taste edit dialog** (`TasteFormDialog`): `TasteFormState` type changes sub-score fields from `number` to `number | null`. New brews default to `null`. Editing existing taste loads stored values (non-null = engaged, null = off). Submit handler sends `null` for off sliders.

**When editing existing taste with values:** sliders start engaged at the stored value. Null stored values start as off.

### 2. Ideal Taste Profile on Person Preferences Page

A new "Taste Profile" section on the person preferences page showing the person's ideal sub-score profile as a radar chart.

**Computation:**
- Take the person's top-5 brews by overall score, considering only brews where at least 3 of the 6 sub-score fields (acidity, sweetness, body, bitterness, balance, aftertaste) are non-null
- Tie-breaking: most recent brew wins (by `brewed_at` desc)
- Average each sub-score across those brews, skipping null values per axis
- Per-axis minimum: at least 2 of the qualifying brews must have rated that axis, otherwise that axis is `null` in the profile
- Section minimum: at least 3 qualifying brews required to show the section; otherwise display "Rate more brews to see your taste profile"

**Backend:**
- Extend `GET /optimize/people/{person_id}/preferences` response with new fields on `PersonPreferences` schema:
  ```json
  {
    "taste_profile": {
      "acidity": 6.5,
      "sweetness": 8.0,
      "body": 7.0,
      "bitterness": 3.5,
      "balance": 7.5,
      "aftertaste": 6.0
    },
    "taste_profile_brew_count": 5
  }
  ```
  Per-axis values are `null` when fewer than 2 qualifying brews rated that axis. `taste_profile` is `null` entirely when fewer than 3 qualifying brews exist.

**Frontend:**
- New section on `PersonPreferencesPage` using the existing `TasteRadar` component
- Positioned after Top Beans, before Roast Preference
- Shows "Based on your N best brews" subtitle
- Null axes render as 0 on the radar (the shape shows gaps for unrated dimensions — this is intentional to encourage rating those axes)

### 3. Hybrid Shared/Personalized Optimization

Recommendations start from a shared pool (all people's brews for a bean+setup) and graduate to per-person filtering when enough personal data exists.

**Threshold:** 5 scored brews by the requesting person for this bean+setup combination.

**API change:**
- `POST /optimize/campaigns/{id}/recommend` accepts a JSON body with optional fields:
  ```json
  {
    "person_id": "uuid-or-null",
    "mode": "auto"
  }
  ```
  - `mode` values: `"auto"` (default), `"community"`, `"personal"`
    - `auto`: use personal if person has >= 5 brews for this bean+setup, else community
    - `community`: always use all brews (ignore person filter)
    - `personal`: always filter to this person's brews. If person has 0 scored brews, return 422 with "No measurements for this person."
  - When `person_id` is omitted: always community mode (backward compatible)

**Async job pipeline:**
- `OptimizationJob` model gains two new nullable columns: `person_id: UUID | None` and `optimization_mode: str | None`
- The recommend endpoint stores `person_id` and resolved mode on the job row before kicking off the async task
- The taskiq worker reads `job.person_id` and `job.optimization_mode` to decide measurement filtering

**Broker logic:**
- When `person_id` is set and mode is `"personal"`: add `.where(Brew.person_id == person_id)` to the measurement query
- When mode is `"community"` or `person_id` is null: use existing query (all brews)

**Response metadata:**
- `Recommendation` model gains two new nullable columns: `optimization_mode: str | None` and `personal_brew_count: int | None`
- These are set by the broker after generating the recommendation and returned in `RecommendationRead`
- The `RecommendationRead` schema adds `optimization_mode: str | None` and `personal_brew_count: int | None`

**DB model changes (2 tables, 4 new nullable columns — no migration needed for SQLite):**
- `OptimizationJob`: add `person_id: UUID | None`, `optimization_mode: str | None`
- `Recommendation`: add `optimization_mode: str | None`, `personal_brew_count: int | None`

Campaign model is unchanged. Campaigns stay keyed by `bean_id + brew_setup_id`.

**Frontend badge/toggle:**
- On the suggestion result card in the brew wizard and the campaign detail stats header
- Chip label format:
  - Auto-resolved community: `"Community (3 brews)"` — clicking switches to `"Personal"`
  - Auto-resolved personal: `"Personal (7 brews)"` — clicking switches to `"Community"`
  - User-forced community: `"Community (forced)"` — clicking switches to `"Personal"`
  - User-forced personal: `"Personal (7 brews)"` — clicking switches to `"Community"`
- Selected mode override is stored in `localStorage` with key `beanbay:opt-mode:{campaignId}`
- When in auto mode and the threshold is crossed, the badge transitions automatically and a brief toast notifies: "Switched to personalized suggestions"

### 4. Suggest Flow Changes

The brew wizard's "Get Suggestion" button already knows the selected person (step 0 of the wizard). The `person_id` flows through the **recommend** step (not campaign creation):

1. `BrewWizard` passes `person_id` from `state.setup.person` to `SuggestButton`
2. `SuggestButton` passes `person_id` to `useSuggest` mutation
3. `useSuggest` Step 1 (create/find campaign) is unchanged — no person_id needed
4. `useSuggest` Step 2 (`POST /campaigns/{id}/recommend`) includes `{ person_id, mode }` in the JSON body. `mode` comes from localStorage if the user previously toggled, otherwise `"auto"`
5. Broker filters measurements based on resolved mode
6. `RecommendationRead` response includes `optimization_mode` and `personal_brew_count` for the badge

## Out of Scope

- Multi-objective optimization (Option A) — future work once sub-score data is rich enough
- Deriving implicit preference weights from sub-scores
- Per-person campaign splitting (campaigns remain shared, only measurement filtering changes)

## Files to Change

**Backend — Models:**
- `src/beanbay/models/optimization.py` — add `person_id`, `optimization_mode` to `OptimizationJob`; add `optimization_mode`, `personal_brew_count` to `Recommendation`

**Backend — Schemas:**
- `src/beanbay/schemas/optimization.py` — add `taste_profile` fields to `PersonPreferences`; add `optimization_mode`, `personal_brew_count` to `RecommendationRead`; add `RecommendRequest` body schema with `person_id` and `mode`

**Backend — Endpoints:**
- `src/beanbay/routers/optimize.py` — compute taste profile in preferences endpoint; accept JSON body on recommend endpoint; store person_id/mode on job

**Backend — Broker:**
- `src/beanbay/services/taskiq_broker.py` — person-filtered measurement query; set optimization_mode and personal_brew_count on recommendation

**Frontend — Slider UX:**
- `frontend/src/features/brews/components/BrewStepTaste.tsx` — off-by-default sliders with X reset
- `frontend/src/features/brews/pages/BrewDetailPage.tsx` — same slider behavior in `TasteFormDialog`

**Frontend — Taste Profile:**
- `frontend/src/features/people/pages/PersonPreferencesPage.tsx` — new Taste Profile section with `TasteRadar`

**Frontend — Hybrid Optimization:**
- `frontend/src/features/optimize/hooks.ts` — extend `useSuggest` to pass `person_id`/`mode` in recommend step; extend `Recommendation` type
- `frontend/src/features/optimize/components/SuggestButton.tsx` — accept and pass `person_id`
- `frontend/src/features/optimize/pages/CampaignDetailPage.tsx` — community/personal toggle badge
- `frontend/src/features/brews/components/BrewWizard.tsx` — pass `person_id` from setup step to `SuggestButton`
