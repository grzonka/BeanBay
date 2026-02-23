---
phase: 14-equipment-management
plan: "03"
subsystem: ui-equipment
tags: [fastapi, jinja2, htmx, css, equipment, paper, water-recipe, mineral, crud, tests]

# Dependency graph
requires:
  - phase: 14-02
    provides: Equipment router with grinder/brewer CRUD, equipment page with modal pattern
  - phase: 14-01
    provides: Paper, WaterRecipe models with all fields (description, notes, 7 mineral columns, is_retired)
provides:
  - Paper/filter CRUD at /equipment/papers (create, edit form, update)
  - Water recipe CRUD at /equipment/water-recipes (create, edit form, update) with 7 mineral fields
  - All 4 equipment types fully manageable in the equipment page
  - Expandable mineral details section in water recipe form (<details> element)
  - Compact mineral summary line in water recipe card
  - 17 equipment tests covering all 4 types
affects:
  - 14-04 (brew setup wizard needs paper and water recipe as selectable equipment)
  - 14-05 (retire/restore adds buttons to all 4 card types)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - <details>/<summary> HTML element for expandable mineral details (no JS required)
    - CSS grid for compact mineral input layout (2-col mobile, 3-col wider)
    - Jinja2 list accumulation with {% set _ = minerals.append(...) %} for conditional summary

# File tracking
key-files:
  created:
    - app/templates/equipment/_paper_card.html
    - app/templates/equipment/_paper_form.html
    - app/templates/equipment/_water_card.html
    - app/templates/equipment/_water_form.html
    - tests/test_equipment.py
  modified:
    - app/routers/equipment.py
    - app/templates/equipment/index.html
    - app/static/css/main.css

# Decisions
decisions:
  - id: D01
    choice: Use <details>/<summary> for mineral details collapsible
    rationale: Zero JS needed, native browser behavior, accessible, consistent with plan spec
    alternatives: Custom collapsible-toggle pattern (extra JS), always-visible inputs
  - id: D02
    choice: Show only non-None minerals in water card summary (GH, KH, Ca, Mg, Na, Cl, SO₄)
    rationale: Cards stay compact; minerals are optional so blank is the common case for basic recipes
  - id: D03
    choice: Water card variable named `recipe`, paper card variable named `paper`
    rationale: Mirrors model class names (WaterRecipe → recipe, Paper → paper) for clarity in templates

# Metrics
metrics:
  duration: "~3 minutes"
  completed: "2026-02-23"
---

# Phase 14 Plan 03: Paper/Filter & Water Recipe CRUD Summary

**One-liner:** Paper/filter CRUD (name + description) and water recipe CRUD (name, notes, 7 mineral fields) completing all 4 equipment types, plus 17 tests.

## What Was Built

### Task 1: Paper/Filter CRUD routes and templates
- Added `POST /equipment/papers`, `GET /equipment/papers/{id}/edit`, `POST /equipment/papers/{id}` to `app/routers/equipment.py`
- Created `_paper_card.html`: card with name, optional description in muted text, retired badge, Edit button
- Created `_paper_form.html`: name (required) + description textarea (optional); htmx create / regular POST edit modes
- Updated `index.html`: replaced Papers placeholder with real card loop, Add Paper button, paper-add-modal

### Task 2: Water Recipe CRUD routes and templates
- Added `POST /equipment/water-recipes`, `GET /equipment/water-recipes/{id}/edit`, `POST /equipment/water-recipes/{id}` to router
- All 7 mineral fields (gh, kh, ca, mg, na, cl, so4) accepted as optional `str = Form("")`, parsed via `_parse_float()`
- Created `_water_card.html`: name, notes, compact mineral summary (e.g. "GH: 65 · KH: 40") — only non-None shown
- Created `_water_form.html`: name + notes + `<details>` expandable mineral section with 7 number inputs in a CSS grid
- Updated `index.html`: replaced Water Recipes placeholder with real loop, Add Water Recipe button, water-add-modal
- Extended htmx `afterSwap` handler for paper-empty and water-empty state removal
- Added `.mineral-grid` CSS (2-col mobile, 3-col ≥480px) and `.card-subtitle` to `main.css`

### Task 3: Equipment CRUD tests for all 4 types
17 tests in `tests/test_equipment.py`:

| Test | Covers |
|------|--------|
| `test_equipment_page_loads` | GET /equipment → 200 |
| `test_equipment_page_shows_counts` | All 4 sections visible with fixture data |
| `test_create_grinder_stepped` | POST → 303, stepped dial config in DB |
| `test_create_grinder_stepless` | POST → 303, stepless (step_size is None) |
| `test_edit_grinder` | POST → 303, name + max_value updated |
| `test_edit_grinder_form` | GET form partial with HX-Request |
| `test_create_brewer_with_methods` | POST → 303, method association in DB |
| `test_edit_brewer` | POST → 303, name updated + methods cleared |
| `test_edit_brewer_form` | GET form partial |
| `test_create_paper` | POST → 303, paper in DB, no description |
| `test_create_paper_with_description` | POST → 303, description stored |
| `test_edit_paper` | POST → 303, name + description updated |
| `test_edit_paper_form` | GET form partial |
| `test_create_water_recipe_basic` | POST → 303, name + notes, minerals None |
| `test_create_water_recipe_with_minerals` | POST → 303, all 7 minerals stored |
| `test_edit_water_recipe` | POST → 303, updates + clears minerals |
| `test_edit_water_recipe_form` | GET form partial |

## Verification

- ✅ `pytest tests/test_equipment.py -v` — 17/17 pass
- ✅ `pytest` — 170/170 pass (153 pre-existing + 17 new)
- ✅ All 4 equipment types have working CRUD at /equipment
- ✅ Water recipe mineral details expandable via `<details>` element
- ✅ Equipment page shows all 4 sections with count badges and cards

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Mineral collapsible | `<details>/<summary>` | Zero JS, native browser behavior, accessible |
| Card mineral summary | Only non-None values, joined by ` · ` | Compact cards; blanks are common |
| Variable names | `recipe` for water, `paper` for paper | Mirrors model class names |

## Deviations from Plan

None — plan executed exactly as written.

## Next Phase Readiness

**Ready for 14-04:** Brew setup assembly wizard
- All 4 equipment types now exist with full CRUD
- Equipment models have all needed fields (is_retired, all relationships)
- No blockers identified
