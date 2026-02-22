---
status: diagnosed
trigger: "No UI to clear/deselect the active bean. Once a bean is selected, users are stuck with it until they manually clear the cookie."
created: 2026-02-22T00:00:00Z
updated: 2026-02-22T00:01:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: CONFIRMED — there is no deselect endpoint and no UI affordance to clear the active bean cookie
test: searched all routers and templates for any deactivate/deselect/clear-cookie logic
expecting: n/a — root cause confirmed
next_action: return diagnosis

## Symptoms

expected: Users should be able to deselect/clear the currently active bean from the UI
actual: Once a bean is selected, there is no UI to deselect it — users must manually clear the cookie
errors: none (missing feature, not a runtime error)
reproduction: Select any bean via "Set Active" → observe there is no "Deselect", "Clear", or "Remove Active" button anywhere
started: always — never implemented

## Eliminated

- hypothesis: deselect endpoint exists but is not linked from the UI
  evidence: full-codebase grep for deactivate/deselect/clear-cookie/delete-cookie found zero matches in any router or template
  timestamp: 2026-02-22T00:01:00Z

- hypothesis: brew.py manages the cookie lifecycle and might clear it
  evidence: brew.py reads the cookie in `_get_active_bean()` but never calls `response.delete_cookie()` or `set_cookie()` — it only redirects if no bean is active
  timestamp: 2026-02-22T00:01:00Z

## Evidence

- timestamp: 2026-02-22T00:00:30Z
  checked: app/routers/beans.py — all route definitions
  found: One `/beans/{bean_id}/activate` POST endpoint (line 173) that calls `response.set_cookie("active_bean_id", ...)` with a 1-year max_age. No corresponding deactivate/clear endpoint exists anywhere in the file.
  implication: The cookie-set path is fully implemented; the cookie-clear path is entirely absent.

- timestamp: 2026-02-22T00:00:35Z
  checked: app/routers/brew.py — full file
  found: `_get_active_bean()` reads the cookie (line 32–36). All brew routes redirect to /beans if no active bean exists. No call to `response.delete_cookie()` or any cookie mutation anywhere in the file.
  implication: brew.py treats the active bean as a read-only dependency; it never participates in clearing it.

- timestamp: 2026-02-22T00:00:40Z
  checked: app/templates/beans/detail.html — page-header section (lines 8–15)
  found: When the bean IS the active bean, the header shows `<span class="badge badge-active">Active</span>` (line 13). When it is NOT active, it shows a "Set Active" form/button (lines 9–11). There is no "Deselect" or "Clear" affordance in either branch.
  implication: The active-bean detail page is the single most natural place to add a deselect action, but it is missing.

- timestamp: 2026-02-22T00:00:45Z
  checked: app/templates/beans/_bean_card.html — full file
  found: Active beans get a badge (`badge-active`), non-active get nothing. Cards are pure navigation links; no inline activate/deactivate affordance exists.
  implication: A secondary "Deselect" affordance could live here (e.g., a small ✕ next to the Active badge) but currently does not.

- timestamp: 2026-02-22T00:00:50Z
  checked: app/templates/base.html — nav active-bean indicator (lines 19–25)
  found: The nav shows the active bean name as a link to its detail page, or "No bean selected" text. No clear/deselect action is surfaced in the nav.
  implication: A tertiary entry point (e.g., a "✕" next to the active bean name in the nav) could be added here.

- timestamp: 2026-02-22T00:00:55Z
  checked: all templates under app/templates/beans/ and app/templates/brew/
  found: grep for deactivate/deselect/clear returned zero template matches.
  implication: The gap is total — no UI affordance exists anywhere.

## Resolution

root_cause: |
  MISSING FEATURE (never implemented). The app has a complete "activate bean" path:
    - Backend:  POST /beans/{bean_id}/activate  →  set_cookie("active_bean_id", value, max_age=1yr)
    - UI:       "Set Active" button on detail.html when the bean is not currently active
  But there is NO corresponding "deactivate bean" path anywhere:
    - No backend endpoint that calls response.delete_cookie("active_bean_id")
    - No UI button, link, or form that would trigger such an action
  The cookie is set to a 1-year max_age with no programmatic expiry path, so once set it persists until manual browser intervention.

fix: N/A (diagnose only)
verification: N/A
files_changed: []
