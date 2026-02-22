# Phase 11: Brew UX Improvements - Context

**Gathered:** 2026-02-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Brew flow interactions are deliberate and guided — no lazy defaults, no silent dead ends. The taste score slider starts inactive and must be explicitly touched before submission. The "Failed Shot" toggle behavior is preserved. Navigating to /brew without an active bean shows a clear prompt instead of silently redirecting.

</domain>

<decisions>
## Implementation Decisions

### Inactive slider look & feel
- Slider starts greyed out at opacity 0.4 (matching the existing Failed Shot dimming pattern)
- More greyed out than current Failed Shot style if needed — the key is that it looks clearly untouched/inactive
- Thumb remains visible but dimmed — user activates by touching/dragging the slider (any interaction counts)
- Once touched, slider snaps to full opacity and stays active
- A `data-touched` attribute (or similar) tracks whether the user has interacted with it
- This pattern applies on both `recommend.html` and `best.html` forms

### Submit gate behavior
- Submit button is always visible and clickable (not disabled)
- If user tries to submit without touching the taste slider, prevent submission and show an inline message near the slider: "Rate the brew before submitting" (or similar phrasing)
- No toast, no modal — keep it inline and close to the slider so the user sees what needs attention
- Message disappears once the user interacts with the slider

### No-bean prompt on /brew
- Instead of silently redirecting to /beans, render the brew page with a simple inline message
- Small, non-dramatic hint — something like "Pick a bean first" with a link to /beans
- No illustration, no suggested beans list — just text + link within the existing page layout
- Keep it minimal; a larger redesign may come later

### OpenCode's Discretion
- Exact wording of the inline messages
- CSS implementation details for the greyed-out slider
- Whether to use a CSS class or inline styles for the untouched state
- Animation/transition when slider activates (subtle fade-in is fine, or none)

</decisions>

<specifics>
## Specific Ideas

- The inactive slider opacity (0.4) matches the existing Failed Shot toggle pattern already in the codebase — reuse that visual language
- The Failed Shot toggle already sets opacity 0.4 and pointer-events none on the taste group — the inactive-start state should look similar but still allow interaction (pointer-events must remain enabled)

</specifics>

<deferred>
## Deferred Ideas

- Larger /brew page redesign — user mentioned possible future refactor of the no-bean flow

</deferred>

---

*Phase: 11-brew-ux-improvements*
*Context gathered: 2026-02-22*
