# Phase 12: Manual Brew Input - Research

**Researched:** 2026-02-22
**Domain:** Flask/Jinja2/htmx manual brew form, batch delete, adaptive parameter ranges, BayBE integration
**Confidence:** HIGH

## Summary

Phase 12 restructures the brew page into a unified flow (bean picker → mode selection → recipe → feedback → submit) and adds manual brew input, batch delete in history, and adaptive parameter range extension. The existing codebase provides strong foundations: `_recipe_card.html` and `_feedback_panel.html` partials are reusable, the `/brew/record` endpoint already handles all 6 parameters + taste + feedback, and `OptimizerService.rebuild_campaign()` exists for campaign reconstruction after deletes.

Key technical challenges: (1) the `Measurement` model needs an `is_manual` Boolean column (requires Alembic migration), (2) the `recommendation_id` column has a `unique=True` constraint that must be handled for manual brews (use UUID as for best-brew-again), (3) the brew index page needs a bean dropdown selector that can change the active bean cookie without a full page reload, and (4) batch delete must rebuild the BayBE campaign after removing measurements from the database.

**Primary recommendation:** Build incrementally — start with the database migration and model changes, then the unified brew flow restructure, then the manual form, then history badges, then batch delete, then adaptive ranges. Each step is independently testable.

## Standard Stack

### Core (Already in use)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | current | Web framework | Already used throughout |
| Jinja2 | current | Template engine | Already used with FastAPI |
| htmx | 2.0.4 | Dynamic HTML updates | Already loaded in `base.html` via CDN |
| SQLAlchemy | current | ORM | Already used for all models |
| Alembic | current | DB migrations | Already configured in `alembic.ini` |
| BayBE | current | Bayesian optimization | Core dependency, `OptimizerService` wraps it |

### Supporting (No new libraries needed)
This phase requires NO new dependencies. Everything is achievable with the existing stack.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Linked slider+number input | Number-only inputs | Sliders provide visual feedback of range position; linked inputs give precision — use both per CONTEXT decision |
| htmx for bean picker | Full page reload | htmx `hx-post` to `/beans/{id}/activate` already exists and returns OOB swap — reuse this pattern |
| Custom confirm dialog | Browser `confirm()` | Browser native is fine for batch delete; keeps things simple |

## Architecture Patterns

### Current File Structure (relevant files)
```
app/
├── routers/
│   ├── brew.py              # GET /brew, POST /recommend, GET /recommend/{id}, POST /record, GET /best
│   └── history.py           # GET /history, GET /history/shots, GET /history/{id}, GET/POST /history/{id}/edit
├── models/
│   ├── measurement.py       # Measurement model (needs is_manual column)
│   └── bean.py              # Bean model (has parameter_overrides JSON)
├── services/
│   └── optimizer.py          # OptimizerService (has rebuild_campaign, add_measurement)
├── templates/
│   ├── brew/
│   │   ├── index.html        # Brew landing (restructure: add bean picker + 3 mode buttons)
│   │   ├── recommend.html    # Recommendation display + rate form
│   │   ├── best.html         # Best recipe display + rate form
│   │   ├── _recipe_card.html # Reusable recipe params display (read-only)
│   │   ├── _feedback_panel.html  # Reusable feedback: notes, flavors, tags
│   │   └── _recommendation_insights.html
│   └── history/
│       ├── index.html        # History page
│       ├── _shot_list.html   # Shot list partial
│       ├── _shot_row.html    # Individual shot row
│       ├── _shot_modal.html  # Shot detail modal
│       ├── _shot_edit.html   # Shot edit form
│       └── _filter_panel.html
├── static/
│   ├── css/main.css          # All styles (1355 lines)
│   └── js/tags.js            # Tag input + flavor slider + modal logic
└── config.py                 # Settings
```

### Pattern 1: Existing Record Flow (The Gold Standard)
**What:** All brew modes (recommend, best, manual) should funnel through the same `POST /brew/record` endpoint.
**When to use:** Every brew submission.
**Current implementation in `brew.py` lines 191-287:**
```python
@router.post("/record", response_class=HTMLResponse)
async def record_measurement(
    request: Request,
    recommendation_id: str = Form(...),  # UUID — unique per submission
    grind_setting: float = Form(...),
    temperature: float = Form(...),
    preinfusion_pct: float = Form(...),
    dose_in: float = Form(...),
    target_yield: float = Form(...),
    saturation: str = Form(...),
    taste: float = Form(7.0),
    # ... optional fields ...
    db: Session = Depends(get_db),
):
    # Deduplication: skip if recommendation_id already recorded
    existing = db.query(Measurement).filter(
        Measurement.recommendation_id == recommendation_id
    ).first()
    if not existing:
        measurement = Measurement(...)
        db.add(measurement)
        db.commit()
        # Also add to BayBE campaign
        optimizer.add_measurement(bean.id, measurement_data, overrides=bean.parameter_overrides)
```
**Key insight:** The `recommendation_id` serves as an idempotency token. For manual brews, generate a UUID on the manual form page (same pattern as `best.html` line 25: `best_session_id = str(uuid.uuid4())`).

### Pattern 2: Pending Recommendation Storage
**What:** Recommendations are stored to disk via `_save_pending()` and loaded for the rate form.
**Manual brew equivalent:** Manual brews don't need pending storage — the form itself contains all params as form inputs (not hidden fields from a recommendation).

### Pattern 3: Active Bean Cookie Pattern
**What:** Active bean is stored in `active_bean_id` cookie, read via `_get_active_bean()` (beans.py line 20-25).
**For brew page bean picker:** The existing `POST /beans/{id}/activate` endpoint (beans.py line 207-235) sets this cookie. The bean picker dropdown can use `hx-post="/beans/{bean_id}/activate"` to change the active bean, then redirect/reload the brew page.

### Pattern 4: Taste Slider Inactive Pattern (Phase 11)
**What:** Taste slider starts dimmed (`opacity: 0.4`, display "—"), `data-touched="false"`, must be touched before form submission.
**CSS (main.css lines 670-686):**
```css
#taste-group {
  opacity: 0.4;
  transition: opacity 0.2s;
}
#taste-group.touched {
  opacity: 1;
}
.taste-required-msg { color: var(--danger); font-size: var(--text-sm); display: none; }
.taste-required-msg.visible { display: block; }
```
**JS (tags.js lines 216-249):** `initFlavorSliders()` blocks submit if `tasteInput.dataset.touched !== 'true'`.
**Reuse:** The manual brew form should use the exact same pattern — include `#taste-group` with `data-touched="false"` and let `tags.js` handle validation.

### Pattern 5: Badge Styling
**What:** Failed badge in shot rows.
**CSS (main.css line 906-909):**
```css
.badge-failed {
  background: var(--danger);
  color: white;
}
```
**Template (_shot_row.html line 6):**
```html
{% if shot.is_failed %}<span class="badge badge-failed">Failed</span>{% endif %}
```
**For Manual badge:** Add `.badge-manual` with a distinct color (e.g., blue/teal to contrast with red Failed badge), and add `{% if shot.is_manual %}<span class="badge badge-manual">Manual</span>{% endif %}` to `_shot_row.html`.

### Anti-Patterns to Avoid
- **Don't create a separate record endpoint for manual brews** — reuse `POST /brew/record` with an added `is_manual` form field
- **Don't store manual brew params in pending recommendations** — the form has editable inputs, no pending storage needed
- **Don't rebuild campaign synchronously in the request thread for batch delete** — `rebuild_campaign` may take seconds; consider running in thread pool with `asyncio.to_thread()` but the existing `rebuild_campaign` is fast for <100 measurements
- **Don't make the bean picker a separate page** — it should be a dropdown on `/brew` itself

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Campaign rebuild after delete | Custom campaign modification | `OptimizerService.rebuild_campaign()` | Already handles measurements DataFrame, tolerance flag, fingerprinting — exists at optimizer.py line 231-256 |
| Deduplication on record | Custom dedup logic | Existing `recommendation_id` unique constraint | Already in `record_measurement()` — just generate UUID for manual brews |
| Taste slider validation | Custom JS validation | Existing `initFlavorSliders()` in `tags.js` | Already blocks submit when `data-touched !== 'true'` |
| Flavor dimension submission | Custom handling | Existing `tags.js` name-stripping on untouched sliders | Lines 233-239 of tags.js already strip name attr from untouched sliders |
| Bean activation | Custom cookie logic | Existing `POST /beans/{id}/activate` | Already sets cookie with 1-year expiry |
| Parameter bounds resolution | Custom bounds logic | `_resolve_bounds()` in optimizer.py | Merges overrides onto DEFAULT_BOUNDS |

## Common Pitfalls

### Pitfall 1: recommendation_id Unique Constraint on Manual Brews
**What goes wrong:** The `Measurement.recommendation_id` column is `unique=True` (measurement.py line 12). Manual brews don't have a "recommendation", but still need a unique ID for dedup.
**Why it happens:** The field was designed for BayBE recommendations only.
**How to avoid:** Generate a UUID for each manual brew form page load (same pattern as `best.html` — `best_session_id = str(uuid.uuid4())`). Pass it as a hidden field in the manual form.
**Warning signs:** IntegrityError on second manual brew submission.

### Pitfall 2: Bean Picker Changes Active Bean but Page State Gets Stale
**What goes wrong:** User changes bean in dropdown → cookie updates → but the manual form still shows the old bean's parameter ranges.
**Why it happens:** Cookie is set server-side but the page isn't refreshed.
**How to avoid:** When bean picker changes the active bean, redirect or reload the brew page so parameter ranges update. Use `hx-post` + redirect (303) or `hx-get` to reload the brew index.
**Warning signs:** Manual form sliders showing wrong ranges for the newly selected bean.

### Pitfall 3: Batch Delete Must Rebuild BayBE Campaign
**What goes wrong:** Deleting measurements from the database without rebuilding the BayBE campaign means the optimizer still "remembers" the deleted data points.
**Why it happens:** BayBE campaigns store measurements internally. Simply deleting from SQLite doesn't affect the campaign JSON on disk.
**How to avoid:** After deleting measurements from DB, call `optimizer.rebuild_campaign(bean_id, remaining_measurements_df, overrides)`. Since deletes may span multiple beans, rebuild all affected campaigns.
**Warning signs:** Optimizer recommendations still influenced by deleted data.

### Pitfall 4: Adaptive Range Extension Must Happen Before Record
**What goes wrong:** User enters a value outside the bean's parameter range, submits → `add_measurement()` is called with data outside campaign bounds → BayBE may reject or mishandle it.
**Why it happens:** `add_measurement()` in the current code doesn't use `numerical_measurements_must_be_within_tolerance=False` (only `rebuild_campaign` and `get_or_create_campaign` do).
**How to avoid:** Two approaches: (a) extend parameter_overrides BEFORE calling record, or (b) modify `add_measurement()` to pass `numerical_measurements_must_be_within_tolerance=False`. Approach (a) is cleaner — the CONTEXT decision says to prompt user and update `Bean.parameter_overrides` before submission.
**Warning signs:** BayBE ValueError or silently dropped measurement data.

### Pitfall 5: Toggle Switch for Saturation Must Submit Correct Values
**What goes wrong:** HTML checkbox submits "on" when checked, nothing when unchecked. But saturation needs "yes"/"no" string values.
**Why it happens:** Default HTML checkbox behavior.
**How to avoid:** Use a hidden input with value "no" + a checkbox with value "yes", or use a `<select>` with two options, or use radio buttons. The CONTEXT says "toggle switch" — implement as a styled checkbox with a hidden fallback input.
**Warning signs:** Saturation value is "on" or missing in the database.

### Pitfall 6: Slider + Number Input Sync
**What goes wrong:** Changing the number input doesn't update the slider, or vice versa.
**Why it happens:** Missing bidirectional `oninput` handlers.
**How to avoid:** Both the slider and number input should share the same `name` attribute (only one submits) or use linked `oninput` handlers that update each other's `.value`.
**Warning signs:** Submitted value doesn't match what user sees.

## Code Examples

### Example 1: Adding is_manual to /brew/record (modify existing endpoint)
```python
# In brew.py — add is_manual parameter to record_measurement
@router.post("/record", response_class=HTMLResponse)
async def record_measurement(
    request: Request,
    recommendation_id: str = Form(...),
    # ... existing params ...
    is_manual: Optional[str] = Form(None),  # NEW — "true" for manual brews
    db: Session = Depends(get_db),
):
    # ... existing logic ...
    if not existing:
        measurement = Measurement(
            # ... existing fields ...
            is_manual=is_manual == "true",  # NEW
        )
```

### Example 2: Alembic Migration for is_manual
```python
# migrations/versions/XXXX_add_is_manual_to_measurements.py
def upgrade() -> None:
    with op.batch_alter_table("measurements", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("is_manual", sa.Boolean(), nullable=True, server_default=sa.text("0"))
        )

def downgrade() -> None:
    with op.batch_alter_table("measurements", schema=None) as batch_op:
        batch_op.drop_column("is_manual")
```

### Example 3: Manual Brew Form Template (new template)
```html
{# brew/manual.html — Manual brew entry with editable params #}
{% extends "base.html" %}

{% block content %}
<div class="page-header">
  <h1 class="page-title">Manual Brew</h1>
  <a href="/brew" class="btn btn-secondary btn-sm">← Back</a>
</div>

<div class="card mb-md">
  <div class="card-subtitle mb-md">{{ active_bean.name }} — manual entry</div>

  <form method="post" action="/brew/record">
    <input type="hidden" name="recommendation_id" value="{{ manual_session_id }}">
    <input type="hidden" name="is_manual" value="true">

    {# Editable recipe params — slider + number input pairs #}
    {% for param in params %}
    <div class="form-group">
      <label class="form-label" for="{{ param.name }}">{{ param.label }}</label>
      <div class="param-input-row">
        <input type="range" id="{{ param.name }}-slider"
          min="{{ param.min }}" max="{{ param.max }}" step="{{ param.step }}"
          value="{{ param.default }}"
          oninput="document.getElementById('{{ param.name }}').value = this.value">
        <input type="number" id="{{ param.name }}" name="{{ param.name }}"
          class="form-input" style="width: 80px;"
          min="{{ param.min }}" max="{{ param.max }}" step="{{ param.step }}"
          value="{{ param.default }}"
          oninput="document.getElementById('{{ param.name }}-slider').value = this.value">
        <span class="recipe-unit">{{ param.unit }}</span>
      </div>
    </div>
    {% endfor %}

    {# Saturation toggle #}
    <div class="form-group">
      <label class="form-label">Saturation</label>
      <input type="hidden" name="saturation" value="no">
      <label class="failed-toggle">
        <input type="checkbox" name="saturation" value="yes"
          {{ 'checked' if default_saturation == 'yes' else '' }}>
        <span>Saturation: Yes</span>
      </label>
    </div>

    {# Taste slider (Phase 11 inactive pattern) #}
    <div class="form-group" id="taste-group">
      <label class="form-label" for="taste">
        Taste Score: <strong id="taste-display">—</strong> / 10
      </label>
      <input type="range" id="taste" name="taste"
        class="score-slider form-input"
        min="1" max="10" step="0.5" value="7.0"
        data-touched="false"
        oninput="this.dataset.touched='true'; document.getElementById('taste-group').classList.add('touched'); document.getElementById('taste-display').textContent = this.value">
      <div class="taste-required-msg" id="taste-required-msg">Rate the brew before submitting</div>
    </div>

    {# Failed shot toggle #}
    <div class="form-group">
      <label class="failed-toggle">
        <input type="checkbox" id="is_failed" name="is_failed" value="true"
          onchange="toggleFailed(this)">
        <span class="failed-toggle-label">⚠️ Failed shot</span>
      </label>
    </div>

    {% include "brew/_feedback_panel.html" %}

    <button type="submit" class="btn btn-primary btn-full">Submit Manual Brew</button>
  </form>
</div>
{% endblock %}
```

### Example 4: Bean Picker Dropdown on Brew Index
```html
{# On brew/index.html — bean picker at top #}
<div class="card mb-md">
  <label class="form-label" for="bean-picker">Bean</label>
  <select id="bean-picker" class="form-input"
    onchange="if(this.value) { fetch('/beans/' + this.value + '/activate', {method:'POST'}).then(() => window.location.reload()) }">
    {% for bean in beans %}
    <option value="{{ bean.id }}" {{ 'selected' if active_bean and active_bean.id == bean.id else '' }}>
      {{ bean.name }}
    </option>
    {% endfor %}
  </select>
</div>
```

### Example 5: Batch Delete Route
```python
# In history.py
@router.post("/delete-batch", response_class=HTMLResponse)
async def delete_batch(
    request: Request,
    db: Session = Depends(get_db),
):
    form = await request.form()
    shot_ids = form.getlist("shot_ids")  # List of measurement IDs
    
    if not shot_ids:
        return RedirectResponse(url="/history", status_code=303)
    
    # Find affected bean IDs before deleting
    measurements = db.query(Measurement).filter(Measurement.id.in_(shot_ids)).all()
    affected_beans = {m.bean_id for m in measurements}
    
    # Delete from DB
    db.query(Measurement).filter(Measurement.id.in_(shot_ids)).delete(synchronize_session=False)
    db.commit()
    
    # Rebuild campaigns for affected beans
    optimizer = request.app.state.optimizer
    for bean_id in affected_beans:
        remaining = db.query(Measurement).filter(Measurement.bean_id == bean_id).all()
        bean = db.query(Bean).filter(Bean.id == bean_id).first()
        if remaining:
            df = pd.DataFrame([{
                "grind_setting": m.grind_setting,
                "temperature": m.temperature,
                "preinfusion_pct": m.preinfusion_pct,
                "dose_in": m.dose_in,
                "target_yield": m.target_yield,
                "saturation": m.saturation,
                "taste": m.taste,
            } for m in remaining])
        else:
            df = pd.DataFrame()
        optimizer.rebuild_campaign(
            bean_id, df,
            overrides=bean.parameter_overrides if bean else None
        )
    
    return RedirectResponse(url="/history", status_code=303)
```

### Example 6: Adaptive Range Extension Route
```python
# In brew.py — endpoint to extend parameter ranges
@router.post("/extend-ranges", response_class=HTMLResponse)
async def extend_ranges(
    request: Request,
    db: Session = Depends(get_db),
):
    bean = _require_active_bean(request, db)
    if not bean:
        return RedirectResponse(url="/beans", status_code=303)
    
    form = await request.form()
    overrides = dict(bean.parameter_overrides or {})
    
    # Parse extension requests (e.g., grind_setting_new_min=13, grind_setting_new_max=25)
    for param in DEFAULT_BOUNDS:
        new_min = form.get(f"{param}_new_min")
        new_max = form.get(f"{param}_new_max")
        if new_min or new_max:
            spec = overrides.get(param, {})
            if new_min:
                spec["min"] = float(new_min)
            if new_max:
                spec["max"] = float(new_max)
            overrides[param] = spec
    
    bean.parameter_overrides = overrides if overrides else None
    db.commit()
    
    # Campaign auto-rebuilds via fingerprint change on next use
    return HTMLResponse("OK")  # or return JSON for htmx to process
```

### Example 7: Saturation Toggle with Hidden Input Pattern
```html
{# Hidden input provides "no" default; checkbox overrides to "yes" when checked #}
<input type="hidden" name="saturation" value="no">
<label class="saturation-toggle">
  <input type="checkbox" name="saturation" value="yes"
    {{ 'checked' if default_saturation == 'yes' else '' }}>
  <span class="saturation-toggle-label">Saturation</span>
</label>
```

## Existing Code Map (What Exists and Where)

### Critical Reusable Components

| Component | File | Lines | Reuse Strategy |
|-----------|------|-------|----------------|
| `_recipe_card.html` | `app/templates/brew/_recipe_card.html` | 1-60 | Make conditional: if `editable` is true, render inputs; else render read-only values |
| `_feedback_panel.html` | `app/templates/brew/_feedback_panel.html` | 1-54 | Include identically in manual form (already standalone) |
| `tags.js` | `app/static/js/tags.js` | 1-290 | Already handles brew form tags, edit tags, flavor slider name-stripping, taste validation |
| `toggleFailed()` | `brew/recommend.html` lines 99-121 | Duplicated in `best.html` 103-125 | Extract to shared JS or keep inline (it's 20 lines) |
| `OptimizerService.rebuild_campaign()` | `app/services/optimizer.py` | 231-256 | Use directly for batch delete campaign reconstruction |
| `OptimizerService.add_measurement()` | `app/services/optimizer.py` | 209-229 | Use directly for manual brew BayBE integration |
| `_resolve_bounds()` | `app/services/optimizer.py` | 57-76 | Use to compute slider ranges for manual form |
| `DEFAULT_BOUNDS` | `app/services/optimizer.py` | 34-40 | Import to template context for manual form slider ranges |
| `ROUNDING_RULES` | `app/services/optimizer.py` | 43-49 | Apply to manual form step values |
| `_best_measurement()` | `app/routers/brew.py` | 84-94 | Use for manual form pre-fill logic |
| `_brew_ratio()` | `app/routers/brew.py` | 97-102 | Use for manual form ratio display |
| Badge CSS `.badge-failed` | `app/static/css/main.css` | 906-909 | Copy pattern for `.badge-manual` |

### Database Changes Required

| Change | File | Details |
|--------|------|---------|
| Add `is_manual` column | `app/models/measurement.py` | `is_manual = Column(Boolean, default=False)` |
| Alembic migration | `migrations/versions/XXXX_*.py` | `batch_op.add_column(sa.Column("is_manual", sa.Boolean(), ...))` |

### Routes to Add/Modify

| Route | Action | File |
|-------|--------|------|
| `GET /brew` | MODIFY: Add bean picker dropdown, 3 mode buttons, load all beans | `brew.py` |
| `GET /brew/manual` | ADD: Manual brew form with editable params | `brew.py` |
| `POST /brew/record` | MODIFY: Add `is_manual` form param | `brew.py` |
| `POST /brew/extend-ranges` | ADD: Adaptive range extension endpoint | `brew.py` |
| `POST /history/delete-batch` | ADD: Batch delete with campaign rebuild | `history.py` |

### Templates to Add/Modify

| Template | Action | Details |
|----------|--------|---------|
| `brew/index.html` | MODIFY: Bean picker + 3 mode buttons + Manual Input button | Restructure completely |
| `brew/manual.html` | ADD: Manual brew form with editable slider+number params | New template |
| `brew/_recipe_card.html` | MODIFY: Add editable mode (conditional) OR create `_recipe_card_editable.html` | Support inputs |
| `history/_shot_row.html` | MODIFY: Add Manual badge | Similar to Failed badge |
| `history/_shot_modal.html` | MODIFY: Add Manual badge | Similar to Failed badge |
| `history/index.html` | MODIFY: Add delete mode toggle | New button + JS |
| `history/_shot_row.html` | MODIFY: Add checkbox for delete mode | Conditionally shown |
| `history/_shot_list.html` | MODIFY: Pass delete_mode flag | For conditional checkbox rendering |

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Only BayBE recommendations | Manual + recommended brews | Phase 12 | Users can record any brew, not just optimizer suggestions |
| Redirect to /beans when no bean | Inline prompt on /brew | Phase 11 | No_active_bean pattern already implemented |
| Single delete via bean cascade | Batch delete individual shots | Phase 12 | Users can correct mistakes without losing entire bean |
| Fixed parameter ranges | Adaptive ranges | Phase 12 | Ranges grow when user's real practice exceeds defaults |

## Open Questions

1. **`_recipe_card.html` modification vs. new template**
   - What we know: CONTEXT says "reuse same layout but with editable inputs instead of read-only"
   - What's unclear: Whether to add conditional logic to `_recipe_card.html` (adds complexity to a clean partial) or create a new `_recipe_card_editable.html` (duplication but separation of concerns)
   - Recommendation: Create `_recipe_card_editable.html` as a new partial — the editable version is structurally different (has slider+input pairs, units, step constraints) and wouldn't share much template code with the read-only version

2. **Bean picker implementation detail**
   - What we know: CONTEXT says "dropdown on brew page, pre-selects active bean, changeable without leaving"
   - What's unclear: Whether changing bean should POST to activate endpoint then reload, or use htmx to swap content
   - Recommendation: Use `onchange` → `fetch POST /beans/{id}/activate` → `window.location.reload()` for simplicity. This sets the cookie and refreshes the page with the new bean's data.

3. **`toggleFailed()` duplication**
   - What we know: Identical function in `recommend.html` lines 99-121 and `best.html` lines 103-125
   - What's unclear: Whether to extract to `tags.js` or keep inline
   - Recommendation: Extract to `tags.js` during this phase since manual.html will need it too (avoids 3x duplication)

4. **Batch delete UI trigger pattern**
   - What we know: CONTEXT says "delete mode toggle button, checkboxes appear, confirm dialog"
   - What's unclear: Whether to use htmx or plain JS for the delete mode toggle
   - Recommendation: Use plain JS to toggle checkbox visibility (CSS class toggle), then htmx `hx-post` for the actual delete. The confirm dialog can be browser native `confirm()`.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: All source files read directly from repository
  - `app/routers/brew.py` — full brew flow routes
  - `app/routers/history.py` — full history routes
  - `app/models/measurement.py` — Measurement schema (no is_manual field exists)
  - `app/models/bean.py` — Bean schema with parameter_overrides
  - `app/services/optimizer.py` — OptimizerService with rebuild_campaign, add_measurement, DEFAULT_BOUNDS
  - `app/templates/brew/*.html` — all brew templates
  - `app/templates/history/*.html` — all history templates
  - `app/static/css/main.css` — all styles including badge-failed, taste-group, recipe-params
  - `app/static/js/tags.js` — tag input, flavor slider, taste validation, modal behavior
  - `tests/test_brew.py` — 580 lines of brew tests
  - `tests/test_history.py` — 326 lines of history tests
  - `tests/test_optimizer.py` — 347 lines of optimizer tests

### Secondary (MEDIUM confidence)
- Alembic migration patterns from existing migrations (e.g., `a2f1c3d5e7b9`, `e192b884d9c6`)
- `12-CONTEXT.md` — user decisions from /gsd-discuss-phase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries needed, all tools already in use and verified in codebase
- Architecture: HIGH — patterns directly observed from existing code, file paths and line numbers verified
- Pitfalls: HIGH — identified from actual code constraints (unique constraint, campaign persistence, checkbox behavior)
- Code examples: HIGH — modeled directly on existing patterns in the codebase

**Research date:** 2026-02-22
**Valid until:** 2026-03-22 (stable — Flask/htmx patterns don't change rapidly)
