# Phase 12: Manual Brew Input - Context

**Gathered:** 2026-02-22
**Status:** Ready for planning

<domain>
## Phase Boundary

User can record any brew manually with all 6 recipe parameters and a taste score, and it feeds into BayBE optimization. Manual brews are visually distinguishable in shot history. The brew page is restructured into a unified flow: pick bean → choose mode (Recommend / Best / Manual) → brew & rate.

Additionally: batch delete for individual brews in history (needed as the correction mechanism since params are not editable after submission), and adaptive parameter range extension when manual input exceeds current bean bounds.

</domain>

<decisions>
## Implementation Decisions

### Brew flow restructure
- Unified flow on `/brew`: Bean picker at top → three mode buttons (Get Recommendation, Repeat Best, Manual Input)
- Bean picker is a dropdown on the brew page itself (not a separate page), pre-selects the currently active bean, changeable without leaving
- All three modes follow the same pattern: click → redirect to recipe page → fill in feedback → submit via POST `/brew/record`
- Manual mode redirects to a recipe page with editable fields (same layout as recommendation page but with inputs instead of read-only values)

### Manual parameter input controls
- 5 continuous params (grind, temp, preinfusion, dose, yield): range sliders with a linked number input beside each for direct typing
- Saturation (yes/no): toggle switch
- Pre-fill logic: use best brew's values for the selected bean if one exists, otherwise use midpoint of the bean's parameter range
- Slider ranges are the bean's BayBE campaign ranges (from `parameter_overrides` or `DEFAULT_BOUNDS`)

### Taste slider & feedback
- Taste slider follows Phase 11 inactive pattern: starts dimmed (opacity 0.4, "—"), must be touched before submit is allowed
- Full feedback panel included on manual form: notes, 6 flavor dimension sliders, flavor tags — identical to recommendation form
- Submit goes to the same `/brew/record` endpoint

### Manual brew identity in history
- Small text badge "Manual" on shot rows in history (same style as existing "Failed" badge)
- Shot detail modal is identical to recommendation detail, just with the "Manual" badge added
- No editing of recipe params after submission — use delete for corrections

### Batch delete in history
- Delete mode toggle button in history view
- When active: checkbox appears next to each brew row
- User can select one or many brews
- Confirm dialog: "Delete X brews?"
- On confirm: deletes from database AND removes from BayBE campaign (rebuild campaign from remaining measurements)
- Works for all brews (manual and recommended), not just manual

### Adaptive parameter range extension
- When a manual input value is outside the bean's current parameter range, show a prompt before submission
- Prompt covers all out-of-range params at once: "Extend grind range to 13–25 and temperature to 84–96?"
- If user confirms: update `Bean.parameter_overrides` with new bounds
- Campaign auto-rebuilds on next use (existing `get_or_create_campaign` fingerprint logic handles this), preserving all historical measurements via `numerical_measurements_must_be_within_tolerance=False`

### OpenCode's Discretion
- Exact slider styling and layout within the recipe card
- How the bean picker dropdown is styled
- Delete mode button placement and icon
- Loading/processing states during campaign rebuild
- How the range extension prompt is presented (modal, inline, toast — as long as it blocks submission until resolved)

</decisions>

<specifics>
## Specific Ideas

- Manual mode recipe page should reuse the same `_recipe_card.html` layout but with editable inputs instead of read-only display — keep visual consistency across all three modes
- The `_feedback_panel.html` partial is already reusable — include it identically on the manual form
- Campaign rebuild on delete uses the existing `rebuild_campaign()` method which already accepts a measurements DataFrame
- The "Manual" badge in history should match the existing "Failed" badge styling for consistency

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 12-manual-brew-input*
*Context gathered: 2026-02-22*
