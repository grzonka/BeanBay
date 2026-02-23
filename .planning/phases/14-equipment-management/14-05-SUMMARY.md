---
phase: 14-equipment-management
plan: "05"
subsystem: equipment-lifecycle
tags: [fastapi, sqlalchemy, jinja2, html, css, pytest, retire-restore, brew-setup, cookie]

# Dependency graph
requires:
  - phase: 14-equipment-management
    provides: Full equipment CRUD + brew setup wizard (plans 01-04)
provides:
  - Retire/restore lifecycle for all 5 equipment types (grinder, brewer, paper, water-recipe, setup)
  - Auto-retire cascade: retiring a component auto-retires all setups using it
  - Brew page two-panel layout with setup + bean selection (cookie-persisted)
  - POST /brew/set-setup route for active setup cookie management
  - 23 new tests covering full retire/restore lifecycle, wizard exclusion, brew page integration
affects:
  - Phase 15 (bean bags + coffee identity): equipment context is now fully lifecycle-managed
  - Phase 16 (BayBE integration): brew page now has both setup and bean selection ready

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Cookie-persisted active setup ID (same pattern as active_bean_id in beans router)"
    - "Auto-retire cascade via bulk UPDATE query on BrewSetup table"
    - "Contextual Retire/Restore buttons: show Retire if active, Restore if retired"
    - "Two-panel brew page: setup card + bean card each with inline dropdown selector"

key-files:
  created: []
  modified:
    - app/routers/equipment.py
    - app/routers/brew.py
    - app/templates/brew/index.html
    - app/templates/equipment/_grinder_card.html
    - app/templates/equipment/_brewer_card.html
    - app/templates/equipment/_paper_card.html
    - app/templates/equipment/_water_card.html
    - app/templates/equipment/_setup_card.html
    - app/static/css/main.css
    - tests/test_equipment.py

key-decisions:
  - "Restore does NOT cascade: retiring a component retires setups; restoring does not auto-restore them"
  - "active_setup_id cookie expires 1 year (same as active_bean_id pattern)"
  - "Brew page shows action buttons when bean is selected; setup is optional context for now"
  - "show_retired toggle already existed in equipment/index.html — no changes needed"
  - "setup-card-retired CSS class added for opacity-0.6 visual distinction"

metrics:
  duration: "~30 minutes"
  completed: "2026-02-23"
  tests_before: 170
  tests_after: 193
  tests_added: 23
---

# Phase 14 Plan 05: Retire/Restore Lifecycle + Brew Page Setup Selection Summary

**One-liner:** Retire/restore lifecycle for all equipment with cascade, cookie-based brew page setup selection, and 23 new tests.

## What Was Built

### Task 1: Retire/Restore Lifecycle for All Equipment

Added retire/restore routes to `app/routers/equipment.py` for all 5 equipment types:
- `POST /equipment/grinders/{id}/retire` — sets `is_retired=True`, auto-retires all setups using this grinder
- `POST /equipment/grinders/{id}/restore` — sets `is_retired=False`, does NOT cascade to setups
- Same pattern for brewers, papers, water-recipes, and setups

Auto-retire cascade helpers (`_auto_retire_setups_for_grinder`, etc.) do bulk UPDATE on BrewSetup table filtering by component FK.

Added contextual Retire/Restore buttons to all 5 card templates:
- Active items show a red **Retire** button
- Retired items show a blue **Restore** button
- `_setup_card.html` also gained `setup-card-retired` CSS class and badge display

Added `.setup-card-retired { opacity: 0.6; }` to `main.css`.

### Task 2: Brew Page Setup Selection

Updated `app/routers/brew.py`:
- Added `_get_active_setup()` helper reading `active_setup_id` cookie, filtering retired setups
- Updated `brew_index()` to always render (no redirect), passing `active_setup`, `setups` (non-retired) to template
- Added `POST /brew/set-setup` route — validates setup exists and not retired, sets 1-year cookie

Updated `app/templates/brew/index.html` to two-panel layout:
- **Setup panel**: shows active setup name + components, dropdown to switch
- **Bean panel**: shows active bean name + roaster, dropdown to switch
- Brew action buttons (Get Recommendation, Repeat Best, Manual Input) shown when bean is selected
- Setup is optional context for now (brew actions don't require it yet)

### Task 3: Comprehensive Tests (23 new)

Added to `tests/test_equipment.py`:
- `sample_setup` fixture using all 4 equipment components
- Retire/restore for each type: grinder, brewer, paper, water-recipe, setup (10 tests)
- Cascade: retire grinder/brewer/paper/water → setup auto-retired (4 tests)
- Restore does not cascade: grinder restored → setup stays retired (1 test)
- `show_retired` toggle: retired hidden by default, shown with `?show_retired=true` (2 tests)
- Wizard exclusion: retired grinder/brewer not in wizard options (2 tests)
- Brew page: set-setup cookie, active setup shown, retired ignored, not in selector (4 tests)

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Restore does NOT cascade | Retiring is destructive; restoring should be intentional per-setup |
| active_setup_id cookie 1-year expiry | Same as active_bean_id — persistent across sessions |
| Brew action buttons shown when bean selected (not setup) | Setup is context; bean drives optimization |
| show_retired toggle was pre-existing | Already implemented in 14-01/14-02 — no changes needed |
| Tests check `is_retired` DB state directly | More reliable than HTML assertions for lifecycle tests |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Ruff E712 lint error on `== False` comparison**

- **Found during:** Task 2 commit (pre-commit hook)
- **Issue:** `BrewSetup.is_retired == False` without `# noqa: E712` on the correct line
- **Fix:** Moved `# noqa: E712` comment to the same line as the comparison
- **Files modified:** `app/routers/brew.py`

**2. [Rule 1 - Bug] Test assertion too broad for retired equipment visibility**

- **Found during:** Task 3 test run
- **Issue:** `assert "Comandante C40" not in response.text` failed because the "Add Grinder" modal has `placeholder="e.g. Comandante C40"` always in the HTML
- **Fix:** Changed assertion to check for `"No grinders yet"` empty state (which appears when no active grinders exist) and `"Retired"` badge (for show_retired test)
- **Files modified:** `tests/test_equipment.py`

## Next Phase Readiness

Phase 14 is now complete (5/5 plans done). Ready for:
- **Phase 15**: Bean bags and coffee identity (multiple bags per coffee, bag tracking)
- **Phase 16**: BayBE intelligence integration (transfer learning, cross-bean cold-start)

The brew page setup selection is a foundation for Phase 16 where the active setup context will feed into BayBE's equipment-aware optimization.
