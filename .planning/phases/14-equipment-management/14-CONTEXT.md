# Phase 14: Equipment Management - Context

**Gathered:** 2026-02-23
**Status:** Ready for planning

<domain>
## Phase Boundary

User can create and manage all equipment types (grinders, brewers, papers, water recipes) and assemble them into named brew setups. Includes a unified equipment management page, setup assembly wizard, retire/restore lifecycle, and brew page setup+bean selection UX. Models already exist from Phase 13 — this phase is purely routes, templates, and UI.

</domain>

<decisions>
## Implementation Decisions

### Equipment page structure
- Single page at top-level nav (same level as Beans, History, etc.)
- Nav entry for "Brew" should be renamed to something catchy like "Let's Brew" or similar
- Page has collapsible sections: Brew Setups at top, then Grinders, Brewers, Papers/Filters, Water Recipes below
- Each section header shows count badge (e.g., "Grinders (2)")
- Count badge reflects active count by default; when "show retired" toggle is on, shows "2 active, 1 retired" or similar
- Equipment displayed as cards within each section
- Empty state: guided "start here" flow for first-time users (e.g., "Add your first grinder to get started")

### Equipment forms & modals
- All equipment creation and editing happens in modals (consistent with existing app patterns)
- **Grinder**: name, dial type toggle (stepped vs stepless). Stepped shows: min, max (both inclusive), step size fields. Stepless shows: min, max fields only
- **Brewer**: name, associated method types (multi-select — a brewer can support multiple methods, e.g., Hario Switch)
- **Paper/Filter**: name, optional description
- **Water recipe**: basic view shows name + notes only. Expandable "mineral details" section reveals GH, KH, Ca, Mg, Na, Cl, SO4 fields (all optional). Water is required for setups — user can create a simple "Tap Water" entry
- Editing existing equipment opens the same modal pre-filled

### Brew setup assembly wizard
- Multi-step wizard flow, step order: (1) Pick brewer, (2) Pick grinder, (3) Pick paper/filter (optional — skip allowed), (4) Pick water recipe (required), (5) Name the setup
- Name is last step ("now give it a name")
- Each step shows available equipment of that type to select from
- Small button/link in each step to create new equipment if needed (opens creation modal, then returns to wizard with new item selected)

### Brew page setup & bean selection
- Brew page shows two-panel selection: equipment setup card on one side, selected beans on the other (side-by-side on desktop, stacked on mobile)
- Clicking the setup card opens a selection menu showing all active setups
- Selection menu also has a small button to edit the current setup or create a new one
- Inline edit: user can swap one component (e.g., change the paper). If the resulting combination doesn't match an existing setup, prompt confirmation to create a new setup. User is prompted for a name for the new setup
- Clicking the beans card opens bean selection
- **Default selection behavior**: first time, user is prompted to select (or create if none exist). After that, last-used setup and last-used beans are pre-selected

### Setup card display
- Setup card shows all components as a compact list (each component as a line item — icon or label + name)
- Setup name displayed prominently at top of card
- Optional components (paper) shown only if present

### Equipment lifecycle (retire-only)
- No deletion — retire-only pattern for all equipment and setups
- Retire is a simple toggle/button on the equipment card
- Retired items are hidden from brew selection and from default equipment page view
- "Show retired" toggle on equipment page reveals retired items (grayed out or visually distinct)
- Retiring individual equipment (e.g., selling a grinder) auto-retires all setups that use that equipment
- Retired items are fully preserved in history/analytics — "retired" means "hidden from new brew selection" only
- User can restore/re-enable retired equipment and setups at any time

### OpenCode's Discretion
- Collapsible section implementation (accordion vs independent collapsibles)
- Exact card layout and styling within sections
- Mobile responsiveness approach for the equipment page
- Wizard step indicator design (progress dots, stepper, etc.)
- Icon choices for equipment types
- Exact empty state illustration/copy
- How to handle the brew page two-panel layout on mobile (stacked order, sizing)

</decisions>

<specifics>
## Specific Ideas

- Setup cards should feel like a summary you can glance at — all components listed compactly so you know exactly what the setup involves at a glance
- The brew page should feel like "pick your setup, pick your beans, let's go" — two clear inputs before the recommendations flow starts
- The inline setup editing on the brew page is a key UX differentiator: users shouldn't have to leave the brew flow to tweak their setup. Swap a component, confirm the new combo, name it, keep going
- Water recipe is always required (even if it's just "Tap Water") — this keeps the data model clean for future analytics

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 14-equipment-management*
*Context gathered: 2026-02-23*
