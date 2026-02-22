---
phase: 13-data-model-evolution-bean-metadata
plan: "01"
subsystem: database
tags: [sqlalchemy, orm, models, migrations, bean-metadata, equipment, brew-setup]

# Dependency graph
requires:
  - phase: 01-06-v1-mvp
    provides: Base Bean and Measurement models this extends
provides:
  - BrewMethod, Grinder, Brewer, Paper, WaterRecipe models
  - BrewSetup model linking equipment + brew method
  - Bag model (multiple bags per bean)
  - Bean extended with roast_date, process, variety
  - Measurement extended with brew_setup_id FK (nullable)
affects:
  - 13-02 (Alembic migration uses these models)
  - 13-03 (Bean metadata UI reads these fields)
  - 14 (Equipment CRUD builds on Grinder/Brewer/Paper/WaterRecipe/BrewSetup)
  - 15 (Multi-method brewing links Measurement to BrewSetup)
  - 16 (Transfer learning uses Bean.process + Bean.variety for similarity)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "UUID string PKs via lambda: str(uuid.uuid4()) for all new models"
    - "SQLAlchemy 1.x style: Column() + declarative_base(), not mapped_column()"
    - "Nullable FKs for backward compatibility on Measurement.brew_setup_id"
    - "cascade='all, delete-orphan' on Bean.bags and Bean.measurements"

key-files:
  created:
    - app/models/brew_method.py
    - app/models/equipment.py
    - app/models/brew_setup.py
    - app/models/bag.py
    - tests/test_models.py (extended with 13 new tests)
  modified:
    - app/models/bean.py
    - app/models/measurement.py
    - app/models/__init__.py
    - tests/conftest.py

key-decisions:
  - "BrewSetup requires only brew_method_id; all equipment FKs are optional — allows partial setups"
  - "Measurement.brew_setup_id is nullable — backward compatibility for all existing measurements"
  - "Bean extended fields (roast_date, process, variety) are nullable — no migration data backfill needed"
  - "Bag is a separate model (not inline fields on Bean) — enables multiple bags per coffee with individual cost/date tracking"

patterns-established:
  - "New models go in individual files under app/models/, exported from __init__.py"
  - "All test model imports added to conftest.py so Base.metadata.create_all() registers them in tests"

# Metrics
duration: 15min
completed: 2026-02-22
---

# Phase 13 Plan 01: New SQLAlchemy Models + Extended Bean/Measurement Summary

**9 SQLAlchemy models covering equipment (Grinder, Brewer, Paper, WaterRecipe), brew workflows (BrewMethod, BrewSetup, Bag), and extended Bean/Measurement — the complete data foundation for v0.2.0**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-02-22T00:00:00Z
- **Completed:** 2026-02-22T00:15:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Created 4 new model files: `brew_method.py`, `equipment.py`, `brew_setup.py`, `bag.py` — 9 new SQLAlchemy tables ready
- Extended `Bean` with `roast_date`, `process`, `variety` (all nullable) and `Measurement` with `brew_setup_id` FK (nullable, indexed)
- Added 13 new model tests covering all new models plus extended fields; full suite 144/144 green

## Task Commits

Each task was committed atomically:

1. **Task 1: Create new SQLAlchemy models and extend Bean/Measurement** - `713dfa4` (feat)
2. **Task 2: Add model tests for all Phase 13 models** - `b57034a` (test)

**Plan metadata:** _(docs commit follows)_

## Files Created/Modified

- `app/models/brew_method.py` — BrewMethod model (id, name UNIQUE NOT NULL, created_at)
- `app/models/equipment.py` — Grinder, Brewer, Paper, WaterRecipe models (UUID PK, name NOT NULL, created_at)
- `app/models/brew_setup.py` — BrewSetup with FK to brew_method (required) and all equipment (optional), relationships
- `app/models/bag.py` — Bag with FK to beans, purchase_date, cost, weight_grams, notes; back_populates Bean.bags
- `app/models/bean.py` — Added roast_date (Date), process (String), variety (String), bags relationship
- `app/models/measurement.py` — Added brew_setup_id (String FK, nullable, indexed), brew_setup relationship
- `app/models/__init__.py` — Exports all 9 models
- `tests/conftest.py` — Imports all 9 models so they register with Base for test DB creation
- `tests/test_models.py` — 13 new tests appended (21 total)

## Decisions Made

- **BrewSetup equipment FKs are optional:** Allows partial setups (e.g., only method + grinder, no paper/water). Simplifies creation flow.
- **Measurement.brew_setup_id is nullable:** All existing measurements have no brew setup. Adding a NOT NULL FK would require a data migration now; keeping nullable defers that to Phase 13-02's Alembic migration.
- **Bag as separate model:** Original design considered inline bag fields on Bean, but a separate `Bag` table enables: multiple bags per coffee, per-bag cost/date tracking, and future bag-level analytics. More flexible for transfer learning similarity (more purchase history).

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **13-02 (Alembic migration):** All models exist and import cleanly. Alembic can now `--autogenerate` to create the migration script. Data migration (existing measurements → default espresso setup) can proceed.
- **Blockers:** None.

---
*Phase: 13-data-model-evolution-bean-metadata*
*Completed: 2026-02-22*
