---
phase: 04-shot-history-feedback-depth
plan: 01
subsystem: ui
tags: [feedback-panel, jinja2, vanilla-js, sqlalchemy, fastapi-forms, sqlite]

# Dependency graph
requires:
  - phase: 03-optimization-loop
    provides: POST /brew/record endpoint, recommend.html + best.html brew forms

provides:
  - Reusable _feedback_panel.html partial (collapsible, notes + 6 flavor sliders + tag input)
  - tags.js: tag chip add/remove behavior, max 10 enforcement, untouched slider null semantics
  - flavor_tags STRING column on Measurement model (JSON-encoded list)
  - POST /brew/record extended to accept and persist notes, 6 flavor dimensions, flavor_tags
  - Startup migration for existing databases (ALTER TABLE ADD COLUMN flavor_tags)

affects:
  - 04-shot-history-feedback-depth
  - 05-insights-trust (flavor dimensions + tags available for analysis)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Collapsible panel via .collapsible-toggle / .collapsible-content.open CSS pattern"
    - "Vanilla JS IIFE module pattern for small focused behavior (tags.js)"
    - "Untouched slider null semantics: removeAttribute('name') on form submit"
    - "Startup ALTER TABLE migration for SQLite single-user apps (no Alembic)"
    - "JSON-encoded list in String column for SQLite compatibility"

key-files:
  created:
    - app/templates/brew/_feedback_panel.html
    - app/static/js/tags.js
  modified:
    - app/models/measurement.py
    - app/routers/brew.py
    - app/main.py
    - app/templates/brew/recommend.html
    - app/templates/brew/best.html
    - app/static/css/main.css
    - tests/test_brew.py

key-decisions:
  - "flavor_tags stored as String (JSON-encoded) not JSON column type for SQLite compatibility"
  - "Untouched sliders: removeAttribute('name') on form submit — sends null not 0"
  - "Startup ALTER TABLE migration in lifespan for existing databases without Alembic"

patterns-established:
  - "Feedback panel is always a reusable partial included into forms via Jinja2 include"
  - "Optional form fields default to None — existing test payloads unaffected"

# Metrics
duration: 4min
completed: 2026-02-22
---

# Phase 4 Plan 01: Shot Feedback Panel Summary

**Collapsible feedback panel (notes + 6 flavor sliders + tag input) added to both brew forms, with POST /brew/record persisting all new fields and flavor_tags JSON column added to Measurement**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-22T01:03:56Z
- **Completed:** 2026-02-22T01:07:31Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Added `flavor_tags` STRING column to `Measurement` model with startup migration for existing SQLite databases
- Extended `POST /brew/record` to accept and persist notes, 6 flavor dimensions (clamped 1–5), and flavor_tags (comma-separated string → JSON list, max 10)
- Created `_feedback_panel.html` partial: collapsible toggle (collapsed by default), notes textarea, 6 dimmed flavor sliders (light up when touched), tag input with datalist suggestions
- Created `tags.js`: tag chip add/remove, max 10 enforcement, hidden input sync, form submit hook strips untouched slider names so they submit null
- Wired panel into both `recommend.html` and `best.html` via `{% include %}` with `<script src="/static/js/tags.js">`
- 68 tests pass (65 existing unchanged + 3 new: notes, flavor dimensions, flavor tags)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add flavor_tags column + extend record endpoint** — `830d037` (feat)
2. **Task 2: Create feedback panel partial + wire into brew forms + CSS/JS + tests** — `fe63dad` (feat)

## Files Created/Modified

- `app/models/measurement.py` — Added `flavor_tags = Column(String, nullable=True)` after intensity
- `app/routers/brew.py` — Added `import json`; extended `record_measurement` with 8 optional Form params + `_clamp_flavor` helper; flavor_tags → JSON on save
- `app/main.py` — Startup migration: `inspect(engine).get_columns("measurements")` → `ALTER TABLE ADD COLUMN flavor_tags TEXT` if missing
- `app/templates/brew/_feedback_panel.html` — Reusable collapsible feedback partial (54 lines)
- `app/templates/brew/recommend.html` — Added `{% include "_feedback_panel.html" %}` before Submit + tags.js script tag
- `app/templates/brew/best.html` — Added `{% include "_feedback_panel.html" %}` before Brew Again + tags.js script tag
- `app/static/css/main.css` — Appended ~110 lines: feedback panel, flavor slider, tag chip styles
- `app/static/js/tags.js` — Tag input IIFE module (126 lines)
- `tests/test_brew.py` — Extended `_record_payload` to accept `**kwargs`; added 3 tests

## Decisions Made

- **flavor_tags as String (not JSON column):** SQLite JSON column type has inconsistent behavior across SQLAlchemy versions. String with `json.dumps`/`json.loads` in application code is explicit and reliable.
- **Untouched sliders → null:** Sliders default to value=3 visually but display "-" until touched. On submit, JS strips `name` attribute from untouched sliders so they never override `None` in the DB. This preserves the "untouched = no opinion" semantic.
- **Startup migration pattern:** Single-user home app with no Alembic directory. Using `inspect(engine).get_columns()` + `ALTER TABLE` in lifespan is the established pattern for this codebase (noted in STATE.md: `Base.metadata.create_all()` in lifespan).

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Feedback panel complete and wired into both rating forms
- `flavor_tags`, notes, and 6 flavor dimensions saved to DB
- Ready for `04-02-PLAN.md` (shot history view)

---
*Phase: 04-shot-history-feedback-depth*
*Completed: 2026-02-22*
