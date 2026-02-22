---
phase: 04-shot-history-feedback-depth
plan: 02
subsystem: ui
tags: [history, htmx, jinja2, sqlalchemy, fastapi, filtering]

# Dependency graph
requires:
  - phase: 04-shot-history-feedback-depth
    plan: 01
    provides: Measurement model with flavor_tags + feedback panel

provides:
  - GET /history: full history page with reverse-chronological shot list
  - GET /history/shots: htmx partial for filtered shot list
  - Filter by bean (dropdown) and minimum taste score (dropdown)
  - Bean detail page "View History" link pre-applies bean filter
  - History nav link in base.html
  - Shot row with datetime, taste score, grind setting, failed badge, notes indicator
  - Empty state for no shots / no matching shots

affects:
  - 04-03 (shot detail modal will hook into shot-row hx-get and modal container)
  - 05-insights-trust (history page is foundation for trend views)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "htmx filter pattern: hx-get on select + hx-include for sibling field"
    - "Router-level query enrichment: join Bean to get bean_name per shot"
    - "Collapsible filter panel on mobile, always-visible on desktop via media query"
    - "Progressive enhancement: shot row hx-get ready for Plan 03 modal endpoint"

# File tracking
key-files:
  created:
    - app/routers/history.py
    - app/templates/history/index.html
    - app/templates/history/_filter_panel.html
    - app/templates/history/_shot_list.html
    - app/templates/history/_shot_row.html
    - tests/test_history.py
  modified:
    - app/main.py
    - app/templates/base.html
    - app/templates/beans/detail.html
    - app/static/css/main.css

# Decisions
decisions:
  - id: filter-pattern
    choice: "htmx hx-include on each select to send both filters"
    rationale: "Simpler than a form submit — each dropdown triggers its own request, including the sibling via hx-include selector"
    alternatives: ["Single form with hx-trigger change", "URL param navigation with JS"]
  - id: shot-enrichment
    choice: "Build list of plain dicts in router (not pass ORM objects to templates)"
    rationale: "Avoids LazyLoad issues post-session, makes created_at always a real datetime, consistent with brew router pattern"
    alternatives: ["Pass ORM objects directly", "Use eager loading"]
  - id: min-taste-type
    choice: "min_taste query param as Optional[float], normalized to int for template selected comparison"
    rationale: "URL sends '7' as string; float allows future fractional values; int normalization ensures template selected comparison works correctly"

# Metrics
metrics:
  duration: "~2 min"
  completed: "2026-02-22"
  tasks_total: 2
  tasks_completed: 2
  tests_added: 10
  tests_total: 78
---

# Phase 04 Plan 02: Shot History View Summary

**One-liner:** Reverse-chronological shot history page with htmx-powered bean + taste score filters and bean detail deep-link.

## What Was Built

A fully functional shot history view:

- **`GET /history`** — full page listing all shots newest-first, with collapsible filter panel on mobile
- **`GET /history/shots`** — htmx partial endpoint that re-renders just the shot list when filters change
- **Filter UX** — two `<select>` dropdowns (bean, min taste); each uses `hx-include` to send both values; list updates without page reload
- **Shot row** — shows date/time, taste score, grind setting, bean name; failed badge and notes icon when present
- **Bean pre-select** — navigating from bean detail page via `?bean_id=X` pre-selects that bean in the filter
- **History nav link** — added to `base.html` nav bar after "Brew"
- **Empty state** — different messages for "no shots ever" vs "no shots match filter"
- **Modal scaffold** — `<dialog id="shot-modal">` with `#shot-modal-container` ready for Plan 03's detail endpoint

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 1 | History router + main.py + nav + bean detail link | ae5da9c | history.py, main.py, base.html, beans/detail.html |
| 2 | Templates + CSS + 10 tests | 6a7e9be | 4 templates, main.css, test_history.py |

## Decisions Made

1. **htmx filter pattern:** Each `<select>` uses its own `hx-get` + `hx-include="[name='other_field']"` to send both filters. Simpler than a shared form — no submit button needed, each change triggers immediately.

2. **Shot enrichment in router:** The router builds plain dicts (not ORM objects) with `bean_name` and `brew_ratio` pre-computed. Avoids SQLAlchemy lazy-load issues after session closes, and makes `created_at` reliably a `datetime` object for `.strftime()` in templates.

3. **`min_taste` normalization:** Query param arrives as `Optional[float]`; normalized to `int` when whole number for template `selected` comparison (`filter_min_taste == score` where `score` is an int from Jinja loop).

## Deviations from Plan

None — plan executed exactly as written.

## Test Coverage

10 new tests in `tests/test_history.py`:

| Test | What it verifies |
|------|-----------------|
| `test_history_page_loads` | GET /history returns 200 with "Brew History" |
| `test_history_shows_shots_reverse_chronological` | Newest shot appears first in HTML |
| `test_history_filter_by_bean` | bean_id param excludes other beans' shots |
| `test_history_filter_by_min_taste` | min_taste=7 excludes taste < 7 |
| `test_history_combined_filters` | Both filters applied simultaneously |
| `test_history_empty_state` | No shots → "Start brewing" message |
| `test_history_shows_failed_indicator` | Failed shot shows "Failed" badge |
| `test_history_shows_notes_indicator` | Shot with notes shows notes icon |
| `test_history_bean_preselect` | ?bean_id=X renders that bean as selected |
| `test_history_shots_partial_htmx` | /history/shots returns partial (no DOCTYPE) |

All 78 tests pass (68 from prior plans + 10 new).

## Next Phase Readiness

**Plan 04-03** (shot detail modal) can build directly on:
- `_shot_row.html` already has `hx-get="/history/{{ shot.id }}"` and `hx-target="#shot-modal-container"`
- `index.html` already has `<dialog id="shot-modal">` and `<div id="shot-modal-container">`
- Plan 03 just needs to add `GET /history/{shot_id}` endpoint returning a modal partial
