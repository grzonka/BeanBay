# Requirements Archive: v1 BrewFlow MVP

**Archived:** 2026-02-22
**Status:** SHIPPED

This is the archived requirements specification for v1.
For current requirements, see `.planning/REQUIREMENTS.md` (created for next milestone).

---

# Requirements: BrewFlow

**Defined:** 2026-02-21
**Core Value:** Every espresso shot teaches the system something — the app must make it effortless to capture feedback from a phone at the espresso machine and return increasingly better recommendations.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Bean Management

- [x] **BEAN-01**: User can create a new bean with name and optional roaster/origin
- [x] **BEAN-02**: User can select an active bean for optimization
- [x] **BEAN-03**: User can view list of all beans with shot counts

### Optimization Loop

- [x] **OPT-01**: User can request a BayBE-powered recipe recommendation for the active bean
- [x] **OPT-02**: User can see recommended params (grind, temp, preinfusion%, dose, yield, saturation) in large scannable text
- [x] **OPT-03**: User can see brew ratio (dose:yield) alongside recommendation
- [x] **OPT-04**: User can submit a taste score (1-10, 0.5 steps) after brewing
- [x] **OPT-05**: User can mark a shot as failed (choked/gusher), auto-setting taste to 1
- [x] **OPT-06**: User can view and re-brew the current best recipe with one tap

### Shot Tracking

- [x] **SHOT-01**: User can view shot history for a bean in reverse chronological order
- [x] **SHOT-02**: User can add optional free-text notes to any shot
- [x] **SHOT-03**: User can record actual extraction time in seconds

### Visualization & Insights

- [x] **VIZ-01**: User can see optimization progress chart (cumulative best taste over time)
- [x] **VIZ-02**: User can see why a recipe was suggested (exploring vs exploiting)
- [x] **VIZ-03**: User can optionally rate 6 flavor dimensions (acidity, sweetness, body, bitterness, aroma, intensity) via expandable panel
- [x] **VIZ-04**: User can see parameter exploration heatmaps (grind x temp colored by taste)
- [x] **VIZ-05**: User can see exploration/exploitation balance indicator (how converged the optimizer is)

### Analytics

- [x] **ANLYT-01**: User can compare best recipes across beans side-by-side
- [x] **ANLYT-02**: User can view brew statistics (total shots, averages, personal records, improvement rate)

### Infrastructure

- [x] **INFRA-01**: App has mobile-first responsive layout with large touch targets (48px+)
- [x] **INFRA-02**: App deploys as a single Docker container on Unraid
- [x] **INFRA-03**: App is accessible from any device on the local network

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Tracking Enhancements

- **TRACK-01**: User can record actual extraction time in seconds (D9)

### Multi-User

- **MULTI-01**: Multiple users can have separate accounts and data

### Advanced Optimization

- **ADV-01**: User can customize parameter ranges per bean
- **ADV-02**: Offline caching of last recommendation for network blips

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Bluetooth scale integration (A1) | Massive complexity, patchy WebBluetooth support, out of scope per PROJECT.md |
| Timer/stopwatch during brew (A2) | Complexity, phone near splash zone, time is outcome not BayBE parameter |
| Multi-user auth (A3) | v1 is single-user personal tool on homeserver |
| Custom param ranges per bean (A4) | Breaks BayBE campaign architecture, current ranges cover all cases |
| Photo capture per shot (A5) | Unreliable camera in PWA, slows down quick feedback flow |
| Social/sharing features (A6) | Orthogonal to optimization mission, massive scope |
| Bean database/barcode scanner (A7) | Massive effort, minimal payoff for personal tool |
| Grinder/machine control (A8) | No standard API, most home grinders have manual dials |
| Real-time shot graphing (A9) | Requires BLE pressure transducers, machine-specific |
| Full offline/PWA (A11) | Can't run BayBE in browser, server IS the optimization engine |
| SCA flavor wheel (A10) | Too complex for quick phone input, 6-dimension profile sufficient |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| BEAN-01 | Phase 2 | Complete |
| BEAN-02 | Phase 2 | Complete |
| BEAN-03 | Phase 2 | Complete |
| OPT-01 | Phase 3 | Complete |
| OPT-02 | Phase 3 | Complete |
| OPT-03 | Phase 3 | Complete |
| OPT-04 | Phase 3 | Complete |
| OPT-05 | Phase 3 | Complete |
| OPT-06 | Phase 3 | Complete |
| SHOT-01 | Phase 4 | Complete |
| SHOT-02 | Phase 4 | Complete |
| SHOT-03 | Phase 3 | Complete |
| VIZ-01 | Phase 5 | Complete |
| VIZ-02 | Phase 5 | Complete |
| VIZ-03 | Phase 4 | Complete |
| VIZ-04 | Phase 6 | Complete |
| VIZ-05 | Phase 5 | Complete |
| ANLYT-01 | Phase 6 | Complete |
| ANLYT-02 | Phase 6 | Complete |
| INFRA-01 | Phase 2 | Complete |
| INFRA-02 | Phase 1 | Complete |
| INFRA-03 | Phase 1 | Complete |

**Coverage:**
- v1 requirements: 22 total
- Shipped: 22
- Dropped: 0

---

## Milestone Summary

**Shipped:** 22 of 22 v1 requirements
**Adjusted:** None — all requirements shipped as originally specified
**Dropped:** None

---
*Archived: 2026-02-22 as part of v1 milestone completion*
