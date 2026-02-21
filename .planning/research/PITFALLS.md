# Pitfalls Research

**Domain:** Phone-first espresso optimization webapp with BayBE (Bayesian optimization)
**Researched:** 2026-02-21
**Confidence:** HIGH (verified against existing codebase, BayBE docs, actual campaign JSON files)

---

## Critical Pitfalls

### Pitfall 1: Campaign JSON Files Are ~20MB Per Bean (Verified)

**What goes wrong:** BayBE's `Campaign.to_json()` serializes the *entire* discrete search space experimental representation as a pickled binary blob inside the JSON. With 6 parameters producing 147,840 combinations, the existing campaign JSON for a single bean is **19.9MB**. Every `recommend()` call requires loading this, and every `add_measurements()` call requires saving it. In a webapp, this means:
- Loading a bean = reading 20MB from disk + deserializing
- Saving after rating = writing 20MB to disk
- API response times of 1-5 seconds just for I/O
- With 10 beans, you have ~200MB of campaign files

**Why it happens:** BayBE uses `NumericalDiscreteParameter` with `SearchSpace.from_product()`, which creates a Cartesian product of all parameter values and stores it as an internal DataFrame. The serialization includes this full DataFrame plus computed encodings as pickled numpy arrays (base64-encoded in JSON).

**How to avoid:**
1. **Keep campaigns in memory** during the server process lifecycle. Load on startup or first access, keep in a dict/cache, persist to disk only on mutation. Don't load/save per-request.
2. **Consider `NumericalContinuousParameter`** instead of `NumericalDiscreteParameter` for parameters like grind, temperature, and yield. Continuous parameters don't create a Cartesian product, dramatically reducing campaign size. BayBE then rounds recommendations to your step sizes.
3. **If sticking with discrete:** accept the file size but mitigate with in-memory caching and async writes.

**Warning signs:** Slow API responses (>2s) for "get recommendation" or "submit rating". Large `/data/campaigns/` directory.

**Phase to address:** Phase 1 (core backend). This is an architecture decision that affects everything downstream. Must decide discrete vs continuous parameters before building the API layer.

**Confidence:** HIGH — verified by inspecting actual campaign file: `wc -c data/campaigns/boo_no_waste_super_blend_(jan26).json` = 19,916,553 bytes.

---

### Pitfall 2: BayBE Version Pinning and Breaking Changes Across Serialized Campaigns

**What goes wrong:** Campaign JSON files include pickled Python objects (numpy arrays, pandas DataFrames) that are version-sensitive. If you upgrade BayBE, numpy, or pandas, existing serialized campaigns may fail to deserialize. You lose all optimization history for all beans. The existing `requirements.txt` pins `baybe[chem,simulation]==0.14.2`, but even minor version bumps in numpy/scipy can break pickle compatibility.

**Why it happens:** BayBE's serialization uses Python's pickle for DataFrames inside JSON (the `gASV...` base64 strings visible in the campaign JSON). Pickle is notoriously fragile across versions. BayBE's own CHANGELOG shows the project went from 0.13.0 to 0.14.2 recently with potential serialization changes.

**How to avoid:**
1. **Pin ALL scientific stack versions** in requirements/Docker (numpy, scipy, pandas, torch, botorch — not just BayBE).
2. **Store measurements separately** from campaign state (the existing Marimo app already does this with CSV files — preserve this pattern). If campaign deserialization fails, you can rebuild from measurements.
3. **Add a campaign rebuild mechanism**: given a bean's measurements CSV, recreate a fresh campaign and replay all measurements via `add_measurements()`. This is your disaster recovery.
4. **Version-tag campaign files** so you know which BayBE version created them.

**Warning signs:** `Campaign.from_json()` throws `UnpicklingError`, `ModuleNotFoundError`, or `AttributeError` after dependency updates.

**Phase to address:** Phase 1 (data layer design). The measurements-as-source-of-truth pattern must be designed from the start.

**Confidence:** HIGH — verified by inspecting campaign JSON content showing pickled binary blobs; confirmed by BayBE's `serialize_dataframe`/`deserialize_dataframe` utility pattern in their docs.

---

### Pitfall 3: `recommend()` Blocks for Seconds on CPU (No GPU)

**What goes wrong:** BayBE uses Gaussian Process surrogate models (via BoTorch/PyTorch) for Bayesian optimization. On an Unraid server (likely CPU-only), `recommend()` can take 2-10 seconds depending on the number of measurements and search space size. During this time, the web server thread is blocked. If the user taps "Get Recommendation" and nothing happens for 5 seconds on their phone, they'll tap again, potentially queuing duplicate requests.

**Why it happens:** The GP model fitting involves matrix inversion (O(n³) in measurements), and the acquisition function optimization searches over 147,840 candidates. On CPU without CUDA, PyTorch is significantly slower.

**How to avoid:**
1. **Make recommendation requests async** with immediate UI feedback ("Calculating...") and a polling/websocket pattern to deliver the result.
2. **Add request deduplication** — ignore rapid repeated taps of "Get Recommendation".
3. **Use a task queue** (even simple — just a flag + background thread) to prevent blocking the web server.
4. **Set `allow_recommending_already_recommended=True`** to avoid the `NotEnoughPointsLeftError` exception when the search space gets explored (BayBE issue #733 confirms a bug in the cache check for this flag).
5. **Consider lighter surrogates** for early phases: `RandomForestSurrogate` is faster than `GaussianProcessSurrogate` for initial MVP.

**Warning signs:** Users complaining about "nothing happening" when they tap. Server logs showing recommendation requests taking >3s. Duplicate recommendations appearing.

**Phase to address:** Phase 2 (API layer). Must design the recommendation endpoint as async from the start, not bolt it on later.

**Confidence:** HIGH — BayBE uses BoTorch GP by default (confirmed in docs). Unraid is CPU-only. 147,840-point discrete space confirmed.

---

### Pitfall 4: Accidental Double-Submission of Measurements

**What goes wrong:** User rates a shot, taps "Submit", phone lags or network is slow, user taps again. Two identical measurements get added to the campaign. BayBE's GP model treats these as two independent observations of the same point, which distorts the surrogate model. With only 10-30 total measurements per bean, one duplicate has outsized impact.

**Why it happens:** Phone usage at an espresso machine means wet/distracted hands, poor network conditions, and impatience. The existing Marimo app doesn't face this because it runs locally, but a web app over network will.

**How to avoid:**
1. **Client-side: Disable submit button immediately on tap**, show spinner, re-enable only after server confirms.
2. **Server-side: Idempotency tokens** — generate a unique ID per recommendation, reject duplicate submissions with the same recommendation ID.
3. **Server-side: Timestamp deduplication** — reject measurements for the same bean with identical parameters within N seconds.
4. **UI: Show clear confirmation** ("Shot #7 recorded! Taste: 8") that persists so user knows it worked.

**Warning signs:** Duplicate rows in measurements CSV with identical timestamps (within seconds). Campaign measurement count jumps by 2 unexpectedly.

**Phase to address:** Phase 2 (API + feedback form). Must be built into the API contract and UI from the start.

**Confidence:** HIGH — this is a universal web form pitfall, amplified by the "messy hands at espresso machine" usage context.

---

### Pitfall 5: Search Space Explosion If Parameters Are Added Later

**What goes wrong:** The current 6-parameter discrete space has 147,840 combinations. Adding even one more parameter (e.g., "water_temp_offset" with 5 values) multiplies to 739,200. Campaign JSON would balloon to ~100MB. BayBE's recommendation time scales with search space size. The system becomes unusable.

**Why it happens:** `SearchSpace.from_product()` creates a Cartesian product. Each new parameter multiplies the space. This is manageable for 6 params but goes exponential.

**How to avoid:**
1. **Strongly consider `NumericalContinuousParameter`** for all numeric parameters. Continuous search spaces don't enumerate candidates — they optimize analytically. This eliminates the explosion problem entirely.
2. **If discrete:** Use constraints to prune impossible combinations (e.g., `DiscreteExcludeConstraint` to remove grind/dose/yield combinations that would produce >60s shots).
3. **Set a hard rule:** No new parameters without evaluating search space size impact.
4. **Use BayBE's `SubspaceDiscrete.MemorySize`** to check space size before creating campaigns.

**Warning signs:** Campaign creation taking >10s. JSON files >50MB. Memory usage spiking when loading campaigns.

**Phase to address:** Phase 1 (parameter design decision). This is a one-time architectural choice that's expensive to change later (all existing campaigns become incompatible).

**Confidence:** HIGH — verified: 21 × 11 × 10 × 4 × 8 × 2 = 147,840. Adding a 5-value parameter → 739,200.

---

## Moderate Pitfalls

### Pitfall 6: Taste Score Subjectivity Confuses the Optimizer

**What goes wrong:** User rates Shot #3 as "7" in the morning when they're fresh, and rates an objectively identical shot as "5" after lunch when their palate is fatigued. BayBE treats these as different objective function values for similar parameter regions, creating noise that slows convergence. With espresso optimization, you typically have only 20-40 shots per bean before moving on — every noisy measurement costs.

**Why it happens:** Human taste perception varies by time of day, palate fatigue, mood, and whether you've eaten recently. A 1-10 scale feels precise but is reproducible to maybe ±1.5 points for most people.

**How to avoid:**
1. **Guide the user** with anchor descriptions: "1 = drain pour, 3 = drinkable but flawed, 5 = fine, 7 = good, 9 = exceptional" displayed next to the slider.
2. **Use coarser scoring initially** (1-5 instead of 1-10) to reduce noise, or at least group by half-points.
3. **Show the user their previous ratings** alongside the current one for context calibration.
4. **Track time-of-day** in metadata so patterns can be identified later.
5. **Don't over-index on this** — BayBE's GP model handles noise reasonably well, and espresso optimization is inherently noisy.

**Warning signs:** User complains "I gave that exact recipe a 7 last time but only a 5 now." Optimization progress chart shows regression in best score.

**Phase to address:** Phase 3 (feedback UX refinement). Start with the simple 1-10 slider in Phase 2, add calibration aids in Phase 3.

**Confidence:** MEDIUM — based on domain knowledge of human sensory evaluation. BayBE's GP model does account for noise via its likelihood, but with <30 data points noise impact is significant.

---

### Pitfall 7: Phone UI With Sliders Is Infuriating for Wet/Messy Hands

**What goes wrong:** The existing Marimo app has 7 sliders (taste, acidity, sweetness, body, bitterness, aroma, intensity). On a phone with wet/coffee-ground-covered fingers, sliders are nearly impossible to use accurately. Users will either skip the optional flavor profile entirely (making it useless data), or mis-slide and submit wrong values (adding noise).

**Why it happens:** Slider controls require precise horizontal dragging, which is the worst possible touch interaction for: (a) small screens, (b) imprecise wet fingers, (c) standing at a machine, (d) one-handed operation.

**How to avoid:**
1. **Replace sliders with large tap targets** for the primary taste score: 10 big numbered buttons in a row, or a 5-star component with half-star taps.
2. **Make flavor profile optional AND collapsible** — hidden behind "Add flavor details" expansion. Most shots should be taste-score-only.
3. **Use buttons/segments instead of sliders** for sub-scores: three big buttons labeled "Low / Medium / High" instead of a 1-5 slider.
4. **Minimum touch target: 48x48px** (Apple HIG) or 44pt. 
5. **Consider a simple "better / worse / same" quick rating** relative to the last shot, as an alternative to absolute 1-10 scoring.

**Warning signs:** Usage analytics showing flavor profile fields always at default values. Users only ever rating taste as 1, 5, or 10 (slider stuck at common positions).

**Phase to address:** Phase 2 (core UI). The feedback form is the most-used screen and must be designed phone-first from the start.

**Confidence:** HIGH — standard mobile UX research on touch target sizes (Apple HIG 44pt, Material Design 48dp).

---

### Pitfall 8: Cold Start UX Disaster — "Why Is It Suggesting Random Garbage?"

**What goes wrong:** For a new bean (0 measurements), BayBE uses a random/exploratory recommender. The first 3-5 recommendations will seem random — possibly suggesting extreme parameters (grind 15 with temp 96°C) that produce terrible shots. User doesn't understand why the "AI" is wasting their coffee and time with obviously bad recipes.

**Why it happens:** Bayesian optimization *requires* exploration to build a model. Without data, random sampling is mathematically correct. But users expect the system to be "smart" immediately.

**How to avoid:**
1. **Explain the cold start explicitly** in the UI: "For your first few shots, BrewFlow needs to explore different regions. These may not taste great, but each one teaches the model. After ~5 shots, recommendations will start improving."
2. **Show exploration vs exploitation status**: "Exploring (2/5 initial shots)" → "Learning (building model)" → "Optimizing (recommending based on your data)"
3. **Let users seed with known-good recipes**: "Already have a recipe you like? Enter it as your first measurement to give the optimizer a head start."
4. **Constrain early exploration** to reasonable ranges: Don't let random exploration suggest grind 15 (way too fine for most beans) by narrowing initial parameter bounds.
5. **Use BayBE's `TwoPhaseMetaRecommender`** to explicitly control how many exploration shots happen before switching to BO.

**Warning signs:** Users creating a bean, getting one bad recommendation, and never coming back. "This app is broken" feedback.

**Phase to address:** Phase 2 (recommendation UX). The cold start explanation must be visible on the very first recommendation screen.

**Confidence:** HIGH — BayBE docs confirm `TwoPhaseMetaRecommender` exists and default behavior is random initial recommendations.

---

### Pitfall 9: CSV Append Pattern Corrupts Under Concurrent Access

**What goes wrong:** The existing pattern (`df_row.to_csv(path, mode="a", header=False, index=False)`) appends to CSV files without locking. In a web server context, two rapid requests (e.g., quickly rating two shots) could interleave writes, corrupting the CSV. Also, incomplete writes (server crash mid-write) leave truncated rows.

**Why it happens:** CSV append is not atomic on any filesystem. The Marimo app was single-threaded so this never surfaced, but a web server handles concurrent requests.

**How to avoid:**
1. **Use SQLite instead of CSV** for measurements storage. SQLite handles concurrency correctly, supports atomic writes, and is built into Python. It's the right tool for a single-user-scaling-to-multi-user app.
2. **If keeping CSV:** use file locking (`fcntl.flock` on Linux) and write to a temp file then atomic rename.
3. **Keep CSV as an export format** but not as the primary data store.

**Warning signs:** Garbled rows in CSV files. Missing column values. Pandas `read_csv` throwing `ParserError`.

**Phase to address:** Phase 1 (data layer). Storage layer choice affects everything above it.

**Confidence:** HIGH — this is a well-documented issue with CSV append patterns under concurrent access.

---

### Pitfall 10: Docker Image Bloat From PyTorch/Scientific Stack

**What goes wrong:** BayBE depends on PyTorch, BoTorch, numpy, scipy, pandas, scikit-learn. A naive `pip install baybe` in a Docker image creates a 2-4GB image. On Unraid, this means: slow first pull (20+ minutes on home internet), significant disk usage, slow rebuilds during development.

**Why it happens:** PyTorch alone is ~800MB-2GB depending on whether CUDA is included. The default `pip install torch` includes CUDA support even on CPU-only machines.

**How to avoid:**
1. **Install CPU-only PyTorch** explicitly: `pip install torch --index-url https://download.pytorch.org/whl/cpu` before installing BayBE. This saves ~1GB.
2. **Use multi-stage Docker builds**: build dependencies in a large image, copy only runtime artifacts to a slim image.
3. **Use `baybe` without `[chem,simulation]` extras** — the current requirements install chemistry (rdkit) and simulation extras that aren't needed for the webapp.
4. **Pin and cache aggressively**: Use Docker layer caching for pip install. Separate requirements from app code.
5. **Target 1-1.5GB** as the image size goal (achievable with CPU-only torch + minimal extras).

**Warning signs:** Docker build taking >15 minutes. Image size >3GB. `docker pull` failing due to disk space on Unraid.

**Phase to address:** Phase 4 (Docker/deployment). But the `requirements.txt` must be cleaned up in Phase 1 to avoid the `[chem,simulation]` extras.

**Confidence:** HIGH — standard knowledge about PyTorch Docker images. The current `baybe[chem,simulation]` installs unnecessary dependencies for this use case.

---

## Minor Pitfalls

### Pitfall 11: Charts That Look Great on Desktop, Broken on Phone

**What goes wrong:** The existing Marimo app uses `matplotlib` with `figsize=(12, 4)` — a landscape aspect ratio that requires horizontal scrolling on a phone. Scatter plots with small points are untappable. Color-coded markers are invisible at phone size. Two side-by-side subplots become unreadable.

**How to avoid:**
1. **Use a mobile-first charting library** (Chart.js, Plotly.js, or similar) that renders responsively.
2. **Single-column layout only** on mobile. No side-by-side charts.
3. **Design charts at 375px width** (iPhone SE) first, then scale up.
4. **Use large markers** (≥12px touch area) on scatter plots. Make them tappable to show details.
5. **Avoid colormaps** as the primary encoding — use size + labels on mobile.

**Phase to address:** Phase 3 (visualization). Not needed for MVP but critical for daily usability.

---

### Pitfall 12: Bean Name Slugging Loses Information

**What goes wrong:** The existing `_bean_slug()` function (`name.strip().lower().replace(" ", "_").replace("/", "_")`) converts bean names to filenames. "Ethiopia/Yirgacheffe" and "Ethiopia Yirgacheffe" produce the same slug, causing data collision. Special characters, emojis, or accented characters in bean names cause filesystem issues.

**How to avoid:**
1. **Use UUIDs as identifiers** internally, display names as user-facing labels.
2. **Store name-to-ID mapping** in a database/config rather than deriving filenames from names.
3. **Validate bean names** on input: alphanumeric + spaces + common punctuation only.

**Phase to address:** Phase 1 (data model). Use proper IDs from the start.

---

### Pitfall 13: No Backup/Restore Strategy for Campaign Data

**What goes wrong:** All optimization data lives in flat files on the Docker container's filesystem. If the container is recreated without volume mounts, or the Unraid array has issues, all data is lost. Unlike a cloud app, there's no automatic backup.

**How to avoid:**
1. **Docker volumes** pointing to a persistent Unraid share.
2. **Export endpoint** in the API: download all data as a ZIP.
3. **Measurements as source of truth** (not campaigns) — campaigns can be rebuilt, measurements cannot.
4. **Automated backup** via Unraid's built-in backup tools to another disk/cloud.

**Phase to address:** Phase 4 (deployment). Volume mounts must be correct from day one.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| File-based storage (JSON/CSV) | No database setup, simple | Corruption risk, no queries, no multi-user | MVP only — migrate to SQLite by Phase 2 |
| BayBE campaign as source of truth | Simple: one file per bean | Version fragility, 20MB files, can't query history | Never — always keep measurements as source of truth |
| Synchronous `recommend()` calls | Simple API, no async complexity | 3-10s blocking requests, terrible phone UX | Development/testing only — must be async for production |
| Matplotlib server-side rendering | Works, existing code reusable | Heavy CPU, not interactive, terrible on mobile | Never for webapp — use client-side charting |
| Global bean name slugs as IDs | No ID generation needed | Name collisions, rename impossible | MVP only — migrate to UUID-based IDs early |
| `baybe[chem,simulation]` extras | Copies from existing requirements | +500MB Docker image, unused rdkit dependency | Never — strip immediately |

---

## Integration Gotchas

### BayBE + Web Framework
- **BayBE is not thread-safe.** Campaign objects should not be shared between request threads. Use per-request loading or a single-writer pattern with locks.
- **BayBE imports are slow** (~3-5s first import due to PyTorch). Server startup will be noticeably slow. Use lazy imports or preload at startup.
- **`campaign.recommend()` modifies internal state** (marks points as recommended). If you load, recommend, but don't save, the recommendation tracking is lost. Always save after recommend OR after add_measurements — pick a consistent pattern.

### BayBE + Docker
- **PyTorch detects CUDA at import time.** In Docker, this can cause warnings/errors if no GPU. Set `CUDA_VISIBLE_DEVICES=""` environment variable.
- **Random seeds:** BayBE/PyTorch have their own random state. For reproducible testing, set `torch.manual_seed()` and numpy seed.
- **Memory usage:** Loading a campaign + running recommend can peak at 500MB-1GB RAM. Unraid containers may need explicit memory limits adjusted.

### Single-User to Multi-User Migration
- **Don't embed user ID into the data model later.** Even for v1 single-user, use a `user_id` field (defaulting to a constant) in your database schema. This makes multi-user trivially addable.
- **Session management:** For v1, no auth needed. But don't design the API to assume no auth — use middleware that's easy to extend.
- **Bean ownership:** Each bean belongs to a user. Even in v1, this relationship should exist in the data model.

---

## Performance Traps

| Operation | Expected Time (CPU, Unraid) | Risk | Mitigation |
|-----------|---------------------------|------|------------|
| `Campaign.from_json()` (20MB file) | 1-3s | Blocks every recommendation request | In-memory cache |
| `campaign.recommend()` with 0-3 measurements | 0.5-2s (random/exploration phase) | Acceptable | None needed |
| `campaign.recommend()` with 10-30 measurements | 3-10s (GP fitting + acquisition optimization) | Blocks UI, user retaps | Async endpoint, loading indicator |
| `campaign.recommend()` with 50+ measurements | 10-30s (GP fitting is O(n³)) | Essentially broken | Unlikely to reach 50 per bean |
| `Campaign.to_json()` (20MB file) | 0.5-2s | Blocks after every rating | Async write, in-memory cache |
| BayBE import | 3-5s (first import, PyTorch loading) | Slow server startup | Preload at startup |
| Docker image pull (2-3GB) | 5-30 min (home internet) | Bad first-run experience | Pre-pull, smaller image |

---

## UX Pitfalls

### At-the-Machine Context
- **User is standing**, phone in one hand, portafilter in the other
- **Screen may be wet/foggy** from steam
- **Attention is split** between the machine and the phone
- **Sessions are short** — 60-90 seconds between pulling the shot and wanting the next recipe

### Implications
1. **No scrolling to find the submit button.** Critical actions must be above the fold on the smallest supported phone.
2. **No typing.** Bean selection should be tap-to-select, not type-to-search (keyboard covers half the screen).
3. **No precision.** Big buttons > sliders > text inputs.
4. **Fast feedback.** After submitting a rating, immediately show the next recommendation button. Don't make them scroll up.
5. **Offline tolerance.** If the Unraid server is slow to respond, the UI should not show a blank screen. Show the last recommendation cached locally.

---

## "Looks Done But Isn't" Checklist

- [ ] **"Recommendations work"** — but does the UI explain exploration vs exploitation? Does it handle the 5-second wait?
- [ ] **"Feedback form works"** — but can you use it with wet hands? Is it one-thumb operable?
- [ ] **"Data persists"** — but what happens when BayBE is upgraded? Can you rebuild campaigns from measurements?
- [ ] **"Charts render"** — but on a 375px wide phone screen? Without horizontal scrolling?
- [ ] **"Docker runs"** — but is the image <2GB? Does it use CPU-only PyTorch? Are volumes mounted correctly?
- [ ] **"Bean management works"** — but what about bean name collisions? Can you rename/delete a bean?
- [ ] **"It's fast enough"** — but on Unraid's CPU? After 20 measurements? With the 20MB campaign file?
- [ ] **"Single user works"** — but is user_id in the schema for future multi-user? Are API routes scoped?
- [ ] **"Shot failure tracked"** — but does taste=1 for failures bias the model toward avoiding exploration of nearby regions (which might actually be good)?

---

## Pitfall-to-Phase Mapping

| Phase | Key Pitfalls to Address | Why This Phase |
|-------|------------------------|----------------|
| **Phase 1: Data Layer / Core Backend** | #1 (campaign size), #2 (version fragility), #5 (search space explosion), #9 (CSV corruption), #12 (bean IDs) | Architecture decisions that are expensive to change later |
| **Phase 2: API + Core UI** | #3 (async recommend), #4 (double-submit), #7 (phone UX), #8 (cold start UX) | User-facing interactions must be right from first use |
| **Phase 3: Visualization + Polish** | #6 (taste subjectivity), #11 (mobile charts) | Refinements that improve daily usability |
| **Phase 4: Docker + Deployment** | #10 (image bloat), #13 (backup/restore) | Deployment hardening |

---

## Sources

- **Campaign JSON analysis:** Inspected `data/campaigns/boo_no_waste_super_blend_(jan26).json` — 19,916,553 bytes (verified)
- **Search space calculation:** 21 × 11 × 10 × 4 × 8 × 2 = 147,840 (verified from `my_espresso.py` parameter definitions)
- **BayBE documentation:** https://emdgroup.github.io/baybe/stable/ (serialization, campaigns, async workflows, recommenders)
- **BayBE GitHub issues:** https://github.com/emdgroup/baybe/issues — #733 (recommendation cache bug), #681 (exploration/exploitation ratio), #697 (confidence metrics)
- **BayBE version:** 0.14.2 (from `requirements.txt`)
- **Existing codebase:** `my_espresso.py` (641 lines, Marimo notebook with BayBE integration)
- **Mobile UX standards:** Apple Human Interface Guidelines (44pt touch targets), Material Design (48dp touch targets)

---
*Pitfalls research for: BrewFlow — phone-first espresso optimization webapp with BayBE*
*Researched: 2026-02-21*
