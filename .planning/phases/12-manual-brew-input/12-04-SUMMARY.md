---
phase: 12
plan: 04
title: Adaptive Range Extension
subsystem: brew-ui
tags: [fastapi, jinja2, javascript, forms, json, testing]
depends_on: ["12-02"]
provides: ["POST /brew/extend-ranges", "out-of-range detection JS", "Bean.parameter_overrides updates"]
affects: []
tech-stack:
  added: []
  patterns: ["fetch-then-submit pattern", "data-* attribute driven JS validation", "JSON column update preserving existing keys"]
key-files:
  created: []
  modified:
    - app/routers/brew.py
    - app/templates/brew/manual.html
    - tests/test_brew.py
decisions:
  - "Remove min/max from number inputs so users can type beyond slider range; data-min/data-max used by JS"
  - "Submit interceptor registered before tags.js so it runs first, preventing double-submit on taste validation"
  - "Hidden #is_manual_flag marker lets JS check it's the manual form without parsing form fields"
  - "fetch('/brew/extend-ranges').then(form.submit()) ensures bounds update persists before record route validates"
  - "DEFAULT_BOUNDS imported at module level (not function level) to keep endpoint clean"
metrics:
  duration: "~2 minutes"
  completed: "2026-02-22"
---

# Phase 12 Plan 04: Adaptive Range Extension Summary

**One-liner:** Client-side out-of-range detection with confirm prompt + POST /brew/extend-ranges updates Bean.parameter_overrides before submission.

## What Was Built

### Task 1: POST /brew/extend-ranges endpoint

Added `POST /brew/extend-ranges` to `app/routers/brew.py`:
- Reads form fields `{param}_min` / `{param}_max` for each key in `DEFAULT_BOUNDS`
- Merges into `bean.parameter_overrides` preserving existing overrides for other params
- Commits to DB, returns `{"status": "ok"}` JSON
- Returns 303 → `/beans` if no active bean

`DEFAULT_BOUNDS` added to the import from `app.services.optimizer`.

### Task 2: Client-side out-of-range detection

Updated `app/templates/brew/manual.html`:
- Removed `min`/`max` HTML attributes from all `.param-number` inputs (users can now type values outside the slider range)
- Added `data-min`, `data-max`, `data-param` attributes to each `.param-number` input
- Updated `oninput` on number inputs to clamp slider: `Math.max(s.min, Math.min(s.max, this.value))`
- Added `<input type="hidden" id="is_manual_flag">` as JS marker
- Added `DOMContentLoaded` submit interceptor (registered before `tags.js`):
  - Iterates `.param-number` inputs, checks value vs `data-min`/`data-max`
  - Builds violation list with new `newMin`/`newMax` per parameter
  - Shows `confirm()` prompt listing all violations
  - If confirmed: `fetch('/brew/extend-ranges', {method:'POST', body:extendData}).then(form.submit())`
  - If cancelled: `e.preventDefault()` stops submission

## Test Coverage

4 new tests (39 total in test_brew.py, 130 total):
- `test_extend_ranges_updates_parameter_overrides` — verifies `parameter_overrides` updated in DB
- `test_extend_ranges_preserves_existing_overrides` — pre-seeded temperature overrides survive grind update
- `test_extend_ranges_no_active_bean_redirects` — 303 to /beans without cookie
- `test_manual_form_has_range_data_attributes` — HTML has `data-min`/`data-max`/`data-param`/`is_manual_flag`

## Deviations from Plan

None — plan executed exactly as written.

## Commits

| Hash    | Message                                                         |
|---------|-----------------------------------------------------------------|
| 1324832 | feat(12-04): add POST /brew/extend-ranges endpoint             |
| 4a4955d | feat(12-04): client-side out-of-range detection and range extension |

## Next Phase Readiness

Phase 12 is now complete (4/4 plans). The manual brew flow is fully operational:
- Manual form with full parameter input (plan 12-02)
- Manual badge in history + batch delete (plan 12-03)
- Adaptive range extension when typing beyond bounds (plan 12-04)

v0.1.1 milestone (phases 10–12) is complete.
