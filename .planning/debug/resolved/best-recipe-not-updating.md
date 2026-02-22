---
status: diagnosed
trigger: "After submitting a higher-rated shot, the 'Repeat Best' page still shows the old best recipe (8/10) instead of the new higher-rated one. The best recipe is not updating after new measurements are recorded."
created: 2026-02-22T00:00:00Z
updated: 2026-02-22T00:01:00Z
---

## Current Focus

hypothesis: CONFIRMED — "Brew Again" form uses a stable recommendation_id ("best-{best.id}") which is UNIQUE in the DB, so the second and all subsequent submissions from /brew/best are silently dropped by the deduplication guard in /brew/record.
test: Traced full flow: best.html hardcodes recommendation_id="best-{best.id}", POST /brew/record checks for existing measurement with that id and skips insert if found (line 171-173).
expecting: N/A — root cause confirmed.
next_action: return diagnosis

## Symptoms

expected: After recording a shot with rating > 8/10, /brew/best shows the new higher-rated recipe
actual: /brew/best still shows the old best recipe (8/10) even after a higher-rated shot is submitted
errors: None reported (silent wrong result — no exception, just silently skipped INSERT)
reproduction: Submit a shot with rating > 8 from /brew/best "Brew Again" form a second time
started: Unknown (design defect introduced with the stable recommendation_id approach in best.html)

## Eliminated

- hypothesis: _best_measurement() query is wrong (bad ORDER BY or filter)
  evidence: Query is ORDER BY taste DESC + is_failed==False + .first() — correct. If a new row existed, it would be returned.
  timestamp: 2026-02-22T00:01:00Z

- hypothesis: Caching / session-state issue serving stale HTML
  evidence: No HTTP caching headers or in-memory caching present. Each GET /brew/best issues a fresh DB query. The problem is the new row never gets inserted, not that the query returns stale data.
  timestamp: 2026-02-22T00:01:00Z

- hypothesis: POST /brew/record fails to commit
  evidence: db.commit() is called correctly at line 189. The path works fine for ordinary recommendations. The failure is pre-commit: the deduplication check on line 171 returns an existing row, so the block at lines 175-188 is skipped entirely.
  timestamp: 2026-02-22T00:01:00Z

## Evidence

- timestamp: 2026-02-22T00:00:30Z
  checked: app/templates/brew/best.html line 25
  found: recommendation_id is hardcoded as "best-{{ best.id }}" — a stable, deterministic string tied to the CURRENT best measurement's integer id (e.g. "best-3")
  implication: Every "Brew Again" submission from the best page sends the exact same recommendation_id string

- timestamp: 2026-02-22T00:00:40Z
  checked: app/routers/brew.py lines 170-173
  found: |
    existing = db.query(Measurement).filter(
        Measurement.recommendation_id == recommendation_id
    ).first()
    if not existing:  # <-- entire insert block is inside this guard
  implication: On the FIRST "Brew Again" submit, no existing row exists so the insert succeeds. On EVERY subsequent submit the existing row IS found, the if-branch is False, and the entire insert is silently skipped.

- timestamp: 2026-02-22T00:00:50Z
  checked: app/models/measurement.py line 12 + migrations/versions/87c4e18a3be4_initial_schema.py line 55
  found: recommendation_id has UNIQUE constraint at both the SQLAlchemy model level (unique=True) and the DB schema (UniqueConstraint). Even if the code-level guard were removed, a second INSERT with the same recommendation_id would raise an IntegrityError.
  implication: Two layers of protection against duplicate inserts — both trigger on "best-{id}" because the id never changes

- timestamp: 2026-02-22T00:01:00Z
  checked: best.html lines 23-25 (HTML comment)
  found: Comment reads "Use a stable 'best' recommendation_id so it deduplicates correctly each time" — confirming this was an intentional design decision, but the intent (prevent double-submit of the same brew session) conflicts with the reality (blocks ALL future brew-again sessions)
  implication: The intent was to prevent a double-click / F5 refresh from recording a duplicate. But "stable per best measurement" means any second brew-again attempt is treated as a duplicate — which is wrong.

## Resolution

root_cause: |
  app/templates/brew/best.html line 25 sets recommendation_id="best-{{ best.id }}" — a static, reusable value.
  The deduplication guard in app/routers/brew.py lines 171-173 checks for an existing Measurement with that recommendation_id.
  After the FIRST "Brew Again" submission from /brew/best, a row with recommendation_id="best-3" (or whatever the current best's id is) exists in the DB.
  Every subsequent "Brew Again" submission sends the same "best-3" id, the guard finds the existing row, and the INSERT is silently skipped — no new measurement is saved, so the best recipe never updates.

fix: |
  Replace the stable "best-{best.id}" recommendation_id with a unique per-session value each time the /brew/best page is rendered.
  The simplest approach: generate a fresh UUID in the show_best route and pass it to the template as best_session_id, then use that as recommendation_id in the form. This preserves the double-submit protection (same page load = same UUID) while allowing a new session each page visit.

verification: N/A (diagnose-only mode)
files_changed: []
