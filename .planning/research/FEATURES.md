# Feature Research

**Domain:** Phone-first espresso optimization webapp with Bayesian optimization (BayBE)
**Researched:** 2026-02-21
**Confidence:** HIGH (core features from direct competitor analysis + existing Marimo prototype), MEDIUM (mobile UX patterns from general best practices)

## Competitive Landscape Summary

### Existing Espresso/Coffee Tracking Apps

| App | Strengths | Weaknesses (for BrewFlow's niche) |
|-----|-----------|-----------------------------------|
| **Beanconqueror** | 30+ brew parameters, BT scale integration, bean management, statistics, SCA cupping, open source, free | No optimization engine — purely manual tracking. Massive feature surface = complexity. Native mobile app (Ionic/Capacitor), not a webapp. No recommendation system. |
| **Decent DE1 App** | Real-time flow/pressure/temp graphing, "God Shot" reference overlay, profile mimicry, open source (Tcl/Tk) | Machine-specific (DE1 only). Desktop-first. No Bayesian optimization. Focus is on machine control, not recipe optimization. |
| **Gaggiuino** | Open source shot profiling for Gaggia Classic mods, shot data import to Beanconqueror | Hardware mod community. Not a standalone recipe tracker. |

### Key Observation

**No existing coffee app does AI-powered recipe optimization.** All existing tools are *tracking* apps — they record what you did and let you browse history. None suggest what to try next. This is BrewFlow's fundamental differentiator.

The closest analogues for the optimization UX come from:
- **BayBE's own Streamlit demo** (basic recommend-measure loop UI)
- **Google Vizier** (optimization service with experiment tracking dashboard)
- **Optuna Dashboard** (hyperparameter optimization visualization)
- **Weights & Biases** (experiment tracking with rich parameter visualization)

## Feature Landscape

### Table Stakes (Users Expect These)

Users who track espresso shots expect these features. Missing any = feels incomplete or unusable at the espresso machine.

| # | Feature | Why Expected | Complexity | Dependencies | Notes |
|---|---------|--------------|------------|--------------|-------|
| T1 | **Bean Management** (create, select, list) | Every coffee app has this. Beans are the fundamental organization unit. Each bean gets its own optimization campaign. | Low | None (foundation) | Keep minimal: name + optional roaster/origin. Don't over-engineer — user wants to create a bean in 5 seconds. |
| T2 | **Recipe Recommendation Display** | This IS the app's core purpose. Show what BayBE suggests in a clear, scannable format at the machine. | Low | T1 (need active bean) | Must show: grind setting, temperature, preinfusion%, dose, target yield, saturation. Large, readable text for machine-side viewing. |
| T3 | **Quick Taste Score Input** (1-10) | Core feedback loop. Must be completable in <10 seconds with one hand. Existing app uses slider 1-10 with 0.5 steps. | Low | T2 (need a recommendation to rate) | Slider or large tap targets. Must work with wet/messy hands. Default path = just the taste score + submit. |
| T4 | **Shot History per Bean** | Users need to see what they've tried. Every coffee app (Beanconqueror, Decent) has brew history. Also essential for trusting the optimizer ("what has it seen?"). | Low | T1 | Reverse chronological list. Show params + taste score. Scrollable table or card list. |
| T5 | **Shot Failure Tracking** | Choked shots and gushers are common. Must have a fast way to mark failure (auto-sets taste=1) so BayBE learns to avoid those parameter regions. | Low | T3 | Toggle/button at top of feedback form, before taste slider. "Shot failed" = auto-1 taste, skip flavor profile. Critical for optimization quality. |
| T6 | **Optimization Progress Visualization** | Users need to see the system is learning. "Cumulative best" chart is the standard in optimization tools (Optuna, W&B). Existing Marimo app already has this. | Medium | T4 (need history data) | Line chart: experiment # vs cumulative best taste. Individual shot scores as scattered dots. Target line at 8.5+ ("excellent"). |
| T7 | **Brew Ratio Display** | Every espresso app shows ratio (dose:yield). The existing Marimo app computes this. Espresso community thinks in ratios (1:2, 1:2.5). | Trivial | T2 | Computed from dose_in and target_yield. Display alongside recommendation. |
| T8 | **Responsive Mobile-First Layout** | Phone is the primary device (at the machine). If it doesn't work on a 375px screen with one thumb, it's broken. | Medium | All UI features | Not just "responsive" — designed phone-first, then enhanced for laptop. Large touch targets (min 44px), generous spacing, no tiny text. |

### Differentiators (Competitive Advantage)

Features no existing coffee app has. These are what make BrewFlow unique.

| # | Feature | Value Proposition | Complexity | Dependencies | Notes |
|---|---------|-------------------|------------|--------------|-------|
| D1 | **Transparent Recommendation Reasoning** | "Why this recipe?" — show whether BayBE is exploring (high uncertainty region) vs exploiting (near known good recipes). No coffee app does this. Builds trust in the AI. | Medium | T2, BayBE integration | BayBE's TwoPhaseMetaRecommender naturally has two phases: initial (FPS/random = exploration) and subsequent (BotorchRecommender = exploitation). Surface this. Show uncertainty info if available from the surrogate model. |
| D2 | **Expandable Flavor Profile** | Quick score by default, but optionally expand to rate acidity/sweetness/body/bitterness/aroma/intensity. Tracked for user's records. Beanconqueror has SCA cupping (complex), but no app has this progressive-disclosure pattern optimized for phone. | Low | T3 | Collapsed by default. Expand with single tap. 6 sub-scores (1-5 each). Not fed to BayBE optimizer — purely metadata for user analysis. Key: must NOT slow down the default quick path. |
| D3 | **Parameter Exploration Heatmaps** | Scatter/heatmap of grind vs temperature colored by taste score. Existing Marimo app has basic version. Shows where the optimizer has explored and where the "sweet spot" is forming. Optimization tool staple (Optuna, W&B) but unique in coffee apps. | Medium | T4 (need ≥5 data points to be meaningful) | grind_setting × temperature is the most interesting pair. Could extend to other param pairs. Color = taste score. RdYlGn colormap (red=bad, green=good). |
| D4 | **Cross-Bean Comparison** | Compare best recipes across beans side-by-side. No coffee app does automated comparison. Helps users understand how different beans want different parameters. | Medium | T1, T4 (need multiple beans with data) | Table: bean name, best taste, recipe that achieved it, # experiments to reach it. Optionally: "This bean likes higher temp / finer grind" insights. |
| D5 | **Brew Statistics Dashboard** | Total shots, average taste, personal records, shots per day/week. Beanconqueror has spending/consumption stats. BrewFlow adds optimization-specific stats: convergence speed, improvement rate. | Medium | T4 | Fun/motivating. "You've pulled 47 shots. Your average taste improved from 5.2 to 7.8 over 3 beans." |
| D6 | **Exploration/Exploitation Balance Indicator** | Visual indicator showing whether the system is still exploring broadly or has started converging. Could be as simple as "Early exploration (shot 3/~8 needed)" vs "Converging on optimal recipe". | Medium | BayBE campaign state | Unique to optimization tools, unprecedented in coffee apps. Helps users understand why a recommendation might seem "weird" (it's exploring). Number of experiments relative to search space size gives a rough convergence indicator. |
| D7 | **"Repeat Best" Quick Action** | One-tap to see the current best recipe again (for when you just want a good shot, not an experiment). Different from "get recommendation" which might explore. | Low | T4 (need ≥1 measurement) | Simple query: find max taste row, display its params. Users often want to just make a good shot, not always experiment. |
| D8 | **Notes & Context on Shots** | Free-text notes field per shot. "Channeling on left side", "beans are 14 days post-roast", "rushed the tamp". Beanconqueror has this. Essential for learning. | Low | T3 | Text area, optional. Collapsed or minimal by default on phone. |
| D9 | **Actual Shot Time Tracking** | Record actual extraction time. Not a BayBE parameter (it's an outcome, not a control), but critical context for diagnosing issues. | Low | T3 | Number input, seconds. Beanconqueror and Decent both track this. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem obvious but would hurt the product if built now.

| # | Feature | Why Requested | Why Problematic | Alternative |
|---|---------|---------------|-----------------|-------------|
| A1 | **Bluetooth Scale Integration** | Beanconqueror has it. Precise weight tracking. | Massive complexity: BLE protocol per scale brand, cross-browser BLE support is patchy (WebBluetooth), different scale APIs. Beanconqueror supports 15+ scale models and it's a major maintenance burden. Also: out of scope per PROJECT.md. | Manual weight entry is fine. Users already know their dose (it's their basket size). Yield is targeted on their scale directly. |
| A2 | **Timer / Stopwatch During Brew** | Beanconqueror and Decent have real-time timers. | Adds complexity, requires keeping screen awake, doesn't improve optimization (time is an outcome not a parameter for BayBE). Phone screen near espresso machine splash zone. | Record actual_time as a number after the shot. User reads time from their scale or machine timer. |
| A3 | **Multi-User Auth** | "My partner also makes espresso." | Massive infrastructure change. Auth, sessions, data isolation, RBAC. v1 is explicitly single-user personal tool on homeserver. | Defer to v2+. Single user is fine for personal optimization tool. |
| A4 | **Custom Parameter Ranges per Bean** | "Light roasts need different temp ranges than dark." | Breaks the BayBE campaign architecture (search space is defined at campaign creation). Would need campaign migration or reset. Adds UI complexity. | Start with generous ranges that cover all cases (86-96°C already spans light-dark). Add per-bean customization in v2 if proven needed. Already out of scope per PROJECT.md. |
| A5 | **Photo Capture per Shot** | Beanconqueror does this (puck shots, latte art). | Camera integration in PWA is unreliable. Photos take storage. Doesn't help optimization. Slows down the quick feedback flow. | Optional text notes where user can describe visual issues. |
| A6 | **Social/Sharing Features** | "Share my best recipe." | Social features are a massive product rabbit hole. Moderation, accounts, discovery. Completely orthogonal to the optimization mission. | Export/share via screenshot or copy-to-clipboard of best recipe. |
| A7 | **Coffee Bean Database / Barcode Scanner** | Beanconqueror has roaster database and bean scanning. | Requires maintaining a database of roasters/beans, or integrating external APIs. Huge effort, small payoff for a personal optimization tool. | Free-text bean name input. User types "Ethiopia Yirgacheffe" in 5 seconds. Good enough. |
| A8 | **Automatic Grinder/Machine Control** | "Set my grinder dial from the app." | Hardware integration nightmare. Every grinder is different. No standard API. Most home grinders (including DF83v) have manual dials. | Display the recommended setting clearly. User adjusts their equipment manually. |
| A9 | **Real-time Shot Graphing** | Decent DE1 shows pressure/flow curves live during extraction. | Requires BLE connection to pressure transducers, real-time data streaming, complex charting. Machine-specific. | Out of scope. Focus on the optimization loop, not real-time monitoring. If user has Gaggiuino/Decent, they already have this in their machine's app. |
| A10 | **Flavor Wheel / Tasting Vocabulary** | SCA coffee flavor wheel is industry standard. Beanconqueror has SCA cupping sheets. | Overly complex for quick phone input. SCA cupping has 10+ categories with sub-categories. Slows down the feedback loop. Intimidating for non-professionals. | Simple 6-dimension flavor profile (acidity, sweetness, body, bitterness, aroma, intensity) with 1-5 scales. Expandable but not the default path. |
| A11 | **Offline-First / PWA with Full Offline** | "What if my WiFi is down?" | Service workers + offline data sync + conflict resolution is complex. For a homeserver app, the server IS the optimization engine — you can't run BayBE offline in the browser. | Ensure quick page loads. If server is down, show last cached recommendation. True offline would require architectural redesign. |

## Feature Dependencies

```
Foundation Layer:
  T1 (Bean Management) ─────────────────────────────────┐
       │                                                  │
       ▼                                                  │
  T2 (Recipe Recommendation) ──► T7 (Brew Ratio)         │
       │                                                  │
       ▼                                                  │
  T3 (Quick Taste Score) ──► T5 (Shot Failure)            │
       │                   ──► D2 (Expandable Flavor)     │
       │                   ──► D8 (Notes)                 │
       │                   ──► D9 (Actual Time)           │
       ▼                                                  │
  T4 (Shot History) ◄────────────────────────────────────┘
       │
       ├──► T6 (Optimization Progress Chart)
       ├──► D3 (Parameter Heatmaps)
       ├──► D4 (Cross-Bean Comparison)
       ├──► D5 (Brew Statistics)
       ├──► D6 (Exploration/Exploitation Indicator)
       └──► D7 ("Repeat Best" Action)

Cross-cutting:
  T8 (Mobile-First Layout) ──► applies to ALL features
  D1 (Transparent Reasoning) ──► enhances T2
```

**Critical Path:** T1 → T2 → T3 → T4 → T6

Everything else branches off this core loop. The optimization loop (T1→T2→T3 feeding back to T2) is the MVP.

## MVP Definition

### Launch With (v1.0) — The Core Optimization Loop

**Goal:** Functional recommend → brew → rate → improve cycle on phone.

| Feature | Rationale |
|---------|-----------|
| T1: Bean Management | Foundation. Can't do anything without selecting a bean. |
| T2: Recipe Recommendation Display | The primary value proposition. |
| T3: Quick Taste Score Input | Closes the feedback loop. |
| T4: Shot History (basic) | Users need to see what's been tried. Trust-building. |
| T5: Shot Failure Tracking | Critical for optimization quality (BayBE needs to learn from failures). |
| T7: Brew Ratio Display | Trivial to implement, expected by espresso users. |
| T8: Mobile-First Layout | Primary use case is phone at machine. |
| D8: Notes (basic) | Simple text field, low effort, high value for user context. |
| D9: Actual Shot Time | Simple number input, important context. |

**Estimated scope:** 9 features, primarily the recommend-measure loop with basic history.

### Add After Validation (v1.x) — Insights & Trust

**Goal:** Help users understand and trust the optimization. Add after core loop proves valuable.

| Feature | Rationale | When |
|---------|-----------|------|
| T6: Optimization Progress Chart | Shows the system is learning. Motivating. Already exists in Marimo app. | v1.1 (first analytics addition) |
| D1: Transparent Reasoning | "Why this recipe?" Exploration vs exploitation. Builds trust. | v1.1 (alongside progress chart) |
| D2: Expandable Flavor Profile | Progressive disclosure — doesn't slow default path. Adds depth for engaged users. | v1.1 (UI enhancement to feedback form) |
| D3: Parameter Heatmaps | Where in the parameter space has been explored? Visual understanding of optimization. | v1.2 (needs ≥5 data points per bean to be useful) |
| D6: Exploration/Exploitation Indicator | "Phase: Exploring (3 of ~8 shots)" — manages expectations. | v1.2 (pairs with D1) |
| D7: "Repeat Best" Quick Action | For days when user just wants a good shot, not an experiment. | v1.2 (simple feature, quality of life) |

### Future Consideration (v2+) — Depth & Breadth

| Feature | Rationale | Condition |
|---------|-----------|-----------|
| D4: Cross-Bean Comparison | Needs multiple beans with sufficient data. Niche but delightful. | When ≥3 beans have ≥10 experiments each |
| D5: Brew Statistics Dashboard | Fun but not essential. Build when there's enough data to be interesting. | When total shots > 30 |
| Multi-user support (A3) | Only if a second person actually uses the system. | Proven demand |
| Custom param ranges per bean (A4) | Only if current ranges prove limiting for specific beans. | Proven pain point |
| Offline caching of last recommendation (partial A11) | Quality of life for occasional network blips. | Low priority, nice to have |

## Feature Prioritization Matrix

Plotting Impact (how much value it adds) vs Effort (implementation complexity):

```
                          HIGH IMPACT
                              │
                 T2 (Rec)     │     T8 (Mobile-First)
                 T3 (Score)   │     D1 (Reasoning)
                 T1 (Beans)   │
                              │
                 T5 (Failure) │     T6 (Progress Chart)
LOW EFFORT ───────────────────┼─────────────────────── HIGH EFFORT
                 T7 (Ratio)   │     D3 (Heatmaps)
                 D8 (Notes)   │     D4 (Cross-Bean)
                 D9 (Time)    │     D5 (Statistics)
                 D7 (Best)    │
                              │     A1 (BLE Scales) ← DON'T BUILD
                              │     A3 (Multi-User) ← DON'T BUILD
                 D2 (Flavor)  │     A9 (Live Graphs) ← DON'T BUILD
                              │
                          LOW IMPACT
```

**Sweet spot (top-left quadrant):** T1, T2, T3, T5, T7, D8, D9 — high impact, low effort. These ARE the MVP.

**Worth the effort (top-right):** T8, D1, T6 — high impact but need more design/implementation work. Build right after MVP.

**Quick wins (bottom-left):** D2, D7 — low effort, moderate impact. Add when polishing.

**Avoid (bottom-right):** A1, A3, A9 — high effort, low impact for the optimization mission.

## Espresso-Specific UX Patterns

### Machine-Side Usage Constraints

These patterns are unique to the espresso-at-the-machine context and should inform all UI decisions:

| Constraint | Implication | Design Decision |
|------------|-------------|-----------------|
| **Messy/wet hands** | Can't use precise touch gestures. Coffee grounds on fingers. | Large touch targets (≥48px). No small checkboxes. Sliders with big thumbs. Generous padding between interactive elements. |
| **Standing, phone in one hand** | Thumb-reachable zone matters. Can't type comfortably. | Key actions in bottom half of screen. Minimal text input. Pre-filled values. Big "Submit" button. |
| **Glancing, not reading** | User looks at phone quickly between grinder adjustments. | Large, high-contrast text for recipe params. No walls of text. Icon + number format. |
| **Time pressure** | Shot timing matters. Can't spend 30 seconds navigating. | One-screen workflow. No multi-step wizards for the core loop. ≤3 taps from launch to "next recipe visible". |
| **Steam/splash proximity** | Phone near steam wand and group head. | Not a hardware concern for us, but reinforces: fast interaction, put phone down quickly. |
| **Morning routine** | Users are pre-coffee. Cognitive load must be minimal. | Obvious primary action. No ambiguous choices. Default values pre-filled. |

### Recommended Input Patterns (Phone-First)

| Input Type | Best Pattern | Avoid |
|------------|--------------|-------|
| Taste score (1-10) | Large segmented control or big slider with 0.5 steps | Small number input, stepper with +/- buttons |
| Shot failed toggle | Large, visually distinct toggle at top of form | Checkbox buried among other inputs |
| Flavor sub-scores (1-5) | Compact horizontal slider row or star rating | Dropdowns, number inputs |
| Notes | Expandable text area (collapsed by default) | Always-visible large text area taking up screen space |
| Bean selection | Dropdown with recent beans at top, "+" for new | Full-page bean management screen blocking the main flow |
| "Get Recommendation" | Single prominent button, always visible when bean is active | Buried in a menu |

### Recipe Display Pattern (Machine-Side Reading)

```
┌─────────────────────────────┐
│  Ethiopia Yirgacheffe  ▼    │  ← Bean selector (compact)
├─────────────────────────────┤
│                             │
│  ☕ NEXT RECIPE             │
│                             │
│  Grind    19.5              │  ← Large text, scannable
│  Temp     92°C              │
│  PI       75%               │
│  Dose     19.0g → 42g      │  ← Shows ratio: 1:2.2
│  Soak     yes               │
│                             │
│  🔍 Exploring new region    │  ← D1: Why this recipe
│                             │
│  [ ☕ Brew & Rate ]          │  ← Primary action button
│                             │
│  ⭐ Repeat best (8.5/10)   │  ← D7: Quick action
│                             │
└─────────────────────────────┘
```

### Feedback Form Pattern (Post-Shot, Quick)

```
┌─────────────────────────────┐
│  Rate This Shot             │
├─────────────────────────────┤
│                             │
│  ⚠️ Shot Failed?  [  OFF ]  │  ← Toggle, prominent
│                             │
│  Taste   ●────────○  7.5   │  ← Large slider
│                             │
│  Time    [ 28 ] seconds     │  ← Simple number
│                             │
│  ▶ Flavor Details...        │  ← Collapsed, tap to expand
│  ┌─────────────────────┐    │
│  │ Acid ●──○  Sweet ●──○│   │  ← Only shown if expanded
│  │ Body ●──○  Bitter●──○│   │
│  │ Aroma●──○  Intns ●──○│   │
│  └─────────────────────┘    │
│                             │
│  Notes ▶ (optional)         │  ← Collapsed text area
│                             │
│  [ ✓ Submit & Get Next ]    │  ← BIG button, bottom of screen
│                             │
└─────────────────────────────┘
```

## BayBE-Specific Feature Considerations

### What BayBE Provides That We Should Surface

| BayBE Capability | How to Surface in UI | Confidence |
|-----------------|---------------------|------------|
| **TwoPhaseMetaRecommender** (FPS → Botorch transition) | Show "Phase: Initial exploration" vs "Phase: Bayesian optimization" | HIGH — well-documented in BayBE |
| **Campaign serialization (JSON)** | Backend handles this. No UI needed. Enables persistence across server restarts. | HIGH — already working in Marimo app |
| **Measurements DataFrame** | Shot history table. campaign.measurements gives all recorded data. | HIGH — already working |
| **Batch recommendations** | Could request batch_size>1 for "show me the next 3 options". Not needed for v1 (1 at a time is fine). | MEDIUM — possible future feature |
| **BayBE Insights (SHAP)** | Feature importance: "Grind setting matters most for this bean, temperature second." Very cool for analytics page. | MEDIUM — requires `baybe[insights]` extra. v2+ feature. |
| **Transfer Learning** | Use data from one bean to accelerate optimization of a similar bean. Very powerful but complex UX. | LOW — advanced feature, v2+ at earliest |

### What BayBE Does NOT Provide (We Must Build)

| Need | Solution |
|------|----------|
| Exploration vs exploitation transparency | Infer from recommender phase (initial = exploration) and/or acquisition function values |
| Confidence/uncertainty visualization | Extract posterior mean/variance from surrogate model (possible but not trivial) |
| Convergence detection ("you've found the optimal recipe") | Heuristic: if cumulative best hasn't improved in N shots, likely converged |
| "Repeat best" functionality | Simple: query measurements for max taste, return those params |

## Laptop vs Phone Feature Split

BrewFlow is phone-first but laptop-enhanced. Features should be tagged by primary device:

| Device | Features | Design |
|--------|----------|--------|
| **Phone (at machine)** | T1-T3, T5, T7, D1, D2, D7, D8, D9 | Quick interactions, large targets, minimal scrolling, one-handed |
| **Laptop (coffee analysis)** | T4 (full history), T6, D3, D4, D5, D6 | Rich charts, data tables, comparative views, analytics dashboard |
| **Both** | T8 (responsive) | Same features, adapted layout |

This split naturally suggests a UI architecture with:
- **Phone view:** Compact workflow-focused screens (recommend → rate → repeat)
- **Laptop view:** Dashboard with charts, history, and analytics panels side by side

## Sources

- **Beanconqueror** (beanconqueror.com, github.com/graphefruit/Beanconqueror) — Feature analysis of the dominant open-source coffee tracking app. 694 GitHub stars, 30+ brew parameters, BT device integration. Confidence: HIGH (direct analysis of live product and source code).
- **Decent Espresso DE1 App** (decentespresso.com/overview) — Feature analysis of the most advanced espresso machine control app. Open source (Tcl/Tk), real-time graphing, "God Shot" reference. Confidence: HIGH (official documentation reviewed).
- **BayBE** (github.com/emdgroup/baybe, v0.14.3) — Optimization engine capabilities. Campaign serialization, TwoPhaseMetaRecommender, Insights module. Confidence: HIGH (official docs + existing working Marimo prototype).
- **Existing Marimo Prototype** (my_espresso.py) — Current implementation with 6 parameters, CSV measurements, matplotlib charts, taste+flavor scoring. Confidence: HIGH (direct code review).
- **Optimization UI patterns** — Informed by Optuna Dashboard, Weights & Biases, Google Vizier patterns (cumulative best charts, parameter importance, heatmaps). Confidence: MEDIUM (based on general industry knowledge, not specific tool documentation).
- **Mobile UX patterns for data entry** — Based on general mobile UX best practices (large touch targets, progressive disclosure, thumb zones). Confidence: MEDIUM (established patterns, not espresso-specific research).

---
*Feature research for: BrewFlow — Phone-first espresso optimization webapp*
*Researched: 2026-02-21*
