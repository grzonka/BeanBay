# Phase 4: Shot History & Feedback Depth - Research

**Researched:** 2026-02-22
**Domain:** htmx UI patterns, SQLite schema, mobile-first forms
**Confidence:** HIGH

## Summary

Phase 4 adds shot history browsing, free-text notes, flavor dimension ratings (6 sliders), and flavor descriptor tags to an existing FastAPI/Jinja2/htmx espresso optimization app. The core challenge is UI — building modals, expandable panels, filtered lists, and tag inputs using htmx patterns consistent with the existing codebase.

The existing codebase already has the `notes` column and all 6 flavor dimension columns (`acidity`, `sweetness`, `body`, `bitterness`, `aroma`, `intensity`) in the `Measurement` model and database schema. The only schema addition needed is storing flavor descriptor tags (up to 10 per shot). The recommended approach is a JSON column on the `measurements` table rather than a separate junction table, keeping the single-user app simple.

For UI patterns, the app already uses: htmx for partial swaps (`hx-post`, `hx-target`, `hx-swap`), Jinja2 template partials (underscore-prefixed `_partial.html` files), CSS `.collapsible-toggle`/`.collapsible-content` classes with inline `onclick` JavaScript, and `.score-slider` styled range inputs. Phase 4 should extend these existing patterns rather than introducing new frameworks.

**Primary recommendation:** Use the native HTML `<dialog>` element for the shot detail/edit modal (no extra JS library needed), extend existing collapsible patterns for notes/flavor panels, use htmx `hx-get` with query params for filtered history list, and store flavor tags as a JSON column in SQLite.

## Standard Stack

### Core (already in project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| htmx | 2.0.4 | Dynamic UI updates (partials, modals, filtering) | Already loaded via CDN in base.html |
| FastAPI | current | Backend routing, form handling | Project framework |
| Jinja2 | current | Server-side templates with partials | Project template engine |
| SQLAlchemy | current | ORM with SQLite JSON column support | Project ORM |
| SQLite | bundled | JSON1 extension for tag storage | Project database |

### Supporting (no new dependencies needed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| HTML `<dialog>` | native | Modal dialogs | Shot detail/edit modal — no library needed |
| HTML `<details>` | native | Expandable panels | Alternative to current JS toggle pattern |
| CSS `accent-color` | native | Slider theming | Already used for checkbox, extend to range inputs |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `<dialog>` element | htmx custom modal + Hyperscript | `<dialog>` is native, accessible, handles backdrop/ESC/focus trapping for free — no extra dep |
| JSON column for tags | Separate `shot_tags` junction table | Junction table is overkill for max 10 tags in a single-user app; JSON column is simpler and queryable via SQLite JSON1 |
| Custom tag input JS | A tag library (Tagify, etc.) | Minimal vanilla JS is sufficient for type-to-search with a predefined list; avoids adding a JS dependency |

**Installation:** No new packages required.

## Architecture Patterns

### Recommended Project Structure (new files for Phase 4)
```
app/
├── routers/
│   ├── brew.py           # Modify: add notes/flavor fields to record endpoint
│   └── history.py        # NEW: /history router for shot list, detail, edit
├── templates/
│   ├── history/
│   │   ├── index.html        # Full page: shot list with filter UI
│   │   ├── _shot_list.html   # Partial: the scrollable shot list (htmx target)
│   │   ├── _shot_row.html    # Partial: single shot row in list
│   │   ├── _shot_modal.html  # Partial: modal content loaded via htmx
│   │   ├── _shot_edit.html   # Partial: edit form within modal
│   │   └── _filter_panel.html # Partial: filter controls
│   └── brew/
│       ├── recommend.html    # Modify: add collapsible notes + flavor panel
│       ├── best.html         # Modify: add collapsible notes + flavor panel
│       └── _feedback_panel.html # NEW: reusable notes + flavor + tags panel
├── static/
│   └── css/
│       └── main.css          # Extend: modal, slider, tag styles
└── models/
    └── measurement.py        # Modify: add flavor_tags JSON column
```

### Pattern 1: htmx Modal via `<dialog>` Element
**What:** Load shot detail content into a `<dialog>` element via htmx, then show it with minimal JS.
**When to use:** Shot row click → load detail modal.
**Example:**
```html
<!-- Shot row in list — clicking loads modal content -->
<div class="shot-row"
     hx-get="/history/{{ shot.id }}"
     hx-target="#shot-modal-content"
     hx-swap="innerHTML"
     hx-on::after-swap="document.getElementById('shot-modal').showModal()">
  <!-- row content -->
</div>

<!-- Modal shell (always in DOM, hidden until opened) -->
<dialog id="shot-modal" class="shot-modal">
  <div id="shot-modal-content">
    <!-- htmx loads content here -->
  </div>
</dialog>
```
```javascript
// Close modal — add to page scripts
document.getElementById('shot-modal').addEventListener('click', function(e) {
  if (e.target === this) this.close(); // click outside closes
});
```
**Why:** Native `<dialog>` provides:
- Built-in backdrop (`::backdrop` pseudo-element, styleable)
- Focus trapping (accessibility)
- ESC key closes automatically
- No JavaScript library needed
- `showModal()` makes it truly modal

### Pattern 2: Collapsible Panels (Existing Pattern)
**What:** Expandable sections for notes, flavor dimensions, and tags — collapsed by default.
**When to use:** During shot rating (recommend.html, best.html) and in the edit modal.
**Example (extending existing pattern):**
```html
<!-- Reusable feedback panel partial: _feedback_panel.html -->
<div class="card mt-md">
  <button type="button" class="collapsible-toggle"
    onclick="this.nextElementSibling.classList.toggle('open'); this.setAttribute('aria-expanded', this.nextElementSibling.classList.contains('open'))">
    Notes & Flavor Profile
    <span aria-hidden="true">&#9662;</span>
  </button>
  <div class="collapsible-content">
    <!-- Notes textarea -->
    <div class="form-group">
      <label class="form-label" for="notes">Notes (optional)</label>
      <textarea id="notes" name="notes" class="form-input"
        rows="3" placeholder="Tasting notes, technique observations...">{{ notes or '' }}</textarea>
    </div>

    <!-- Flavor dimensions — 6 sliders -->
    <div class="flavor-dimensions mt-md">
      <div class="form-label mb-sm">Flavor Profile (optional)</div>
      {% for dim in ['acidity', 'sweetness', 'body', 'bitterness', 'aroma', 'intensity'] %}
      <div class="flavor-slider-row">
        <label class="flavor-slider-label" for="{{ dim }}">{{ dim | title }}</label>
        <input type="range" id="{{ dim }}" name="{{ dim }}"
          class="flavor-slider" min="1" max="5" step="1"
          value="{{ values.get(dim, 3) if values.get(dim) else '' }}"
          oninput="this.nextElementSibling.textContent = this.value">
        <span class="flavor-slider-value">{{ values.get(dim, '—') }}</span>
      </div>
      {% endfor %}
    </div>

    <!-- Flavor tags (Phase 4 addition) -->
    <div class="flavor-tags mt-md">
      <label class="form-label">Flavor Tags (optional, up to 10)</label>
      <div class="tag-input-container" id="tag-input-container">
        <div class="tag-list" id="tag-list">
          <!-- existing tags rendered as removable badges -->
        </div>
        <input type="text" class="form-input tag-search"
          id="tag-search" placeholder="Type to search flavors..."
          autocomplete="off">
        <div class="tag-suggestions" id="tag-suggestions" style="display:none;">
          <!-- populated by JS filtering -->
        </div>
      </div>
      <!-- Hidden input holds JSON array of selected tags -->
      <input type="hidden" name="flavor_tags" id="flavor-tags-hidden" value="[]">
    </div>
  </div>
</div>
```

### Pattern 3: htmx Filtered List
**What:** Filter the shot history list by bean and minimum taste score, updating via htmx.
**When to use:** History page filter controls.
**Example:**
```html
<!-- Filter form sends GET with query params, replaces shot list -->
<form hx-get="/history/shots"
      hx-target="#shot-list"
      hx-swap="innerHTML"
      hx-trigger="change from:select, change from:input[type=range]"
      hx-include="[name='bean_id'], [name='min_taste']">
  <div class="form-group">
    <label class="form-label" for="bean_id">Bean</label>
    <select name="bean_id" id="bean_id" class="form-input">
      <option value="">All beans</option>
      {% for bean in beans %}
      <option value="{{ bean.id }}" {{ 'selected' if bean.id == selected_bean_id }}>
        {{ bean.name }}
      </option>
      {% endfor %}
    </select>
  </div>
  <div class="form-group">
    <label class="form-label" for="min_taste">
      Min Taste: <strong id="min-taste-display">1</strong>
    </label>
    <input type="range" name="min_taste" id="min_taste"
      class="score-slider form-input" min="1" max="10" step="0.5" value="1"
      oninput="document.getElementById('min-taste-display').textContent = this.value">
  </div>
</form>

<div id="shot-list">
  {% include "history/_shot_list.html" %}
</div>
```
```python
# Router endpoint returns partial
@router.get("/shots", response_class=HTMLResponse)
async def shot_list_partial(
    request: Request,
    bean_id: str = "",
    min_taste: float = 1.0,
    db: Session = Depends(get_db),
):
    query = db.query(Measurement).order_by(Measurement.created_at.desc())
    if bean_id:
        query = query.filter(Measurement.bean_id == bean_id)
    if min_taste > 1.0:
        query = query.filter(Measurement.taste >= min_taste)
    shots = query.all()
    return templates.TemplateResponse(
        request,
        "history/_shot_list.html",
        {"shots": shots},
    )
```

### Pattern 4: In-Modal Edit via htmx Swap
**What:** Switch between view and edit mode within the modal using htmx.
**When to use:** Edit button in shot detail modal.
**Example:**
```html
<!-- In _shot_modal.html (view mode) -->
<div id="modal-body">
  <h2>Shot Detail</h2>
  <!-- read-only display of shot data -->
  <button class="btn btn-secondary btn-full mt-md"
    hx-get="/history/{{ shot.id }}/edit"
    hx-target="#modal-body"
    hx-swap="innerHTML">
    Edit
  </button>
</div>

<!-- Server returns _shot_edit.html (edit mode) -->
<form hx-post="/history/{{ shot.id }}"
      hx-target="#modal-body"
      hx-swap="innerHTML">
  <!-- editable fields: notes, flavor dimensions, tags -->
  <button type="submit" class="btn btn-primary btn-full">Save</button>
  <button type="button" class="btn btn-secondary btn-full mt-sm"
    hx-get="/history/{{ shot.id }}"
    hx-target="#modal-body"
    hx-swap="innerHTML">
    Cancel
  </button>
</form>
```

### Anti-Patterns to Avoid
- **Don't use full-page redirects for modal interactions:** Use htmx partial swaps to load/update modal content. The existing codebase uses `RedirectResponse(status_code=303)` for form submissions — that pattern is fine for main navigation but modal interactions should use htmx swap.
- **Don't make flavor dimensions required:** They must always be optional. The collapsible panel should never be forced open. If no slider is touched, send null/empty, not a default value.
- **Don't paginate the history list:** Decision says scrollable, no pagination. Use CSS `overflow-y: auto` with a max-height or let the page scroll naturally.
- **Don't add Hyperscript or other JS micro-frameworks:** The project uses vanilla JS for the small interactive bits (slider value display, checkbox toggle). Keep it that way.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Modal dialog | Custom overlay + z-index + focus trap | HTML `<dialog>` element | Native focus trapping, backdrop, ESC handling, accessibility built in |
| Collapsible panel | Custom accordion component | Existing `.collapsible-toggle` / `.collapsible-content` CSS classes | Already in codebase, consistent UX |
| Filtered list update | Manual fetch + DOM manipulation | htmx `hx-get` + `hx-target` + `hx-trigger="change"` | Core htmx pattern, no custom JS needed |
| Range input value display | Custom tooltip/overlay | `oninput` handler updating adjacent `<span>` | Already done this way for taste slider in recommend.html |
| Form field inclusion across elements | Manual FormData construction | htmx `hx-include` attribute | Lets htmx gather values from form fields outside the triggering element |

**Key insight:** This phase is mostly template work. The backend is straightforward CRUD. The UI patterns all exist in htmx's standard toolkit or as native HTML elements. Resist the urge to add JavaScript libraries.

## Common Pitfalls

### Pitfall 1: Flavor Slider Sends Default When Untouched
**What goes wrong:** If a slider defaults to value="3" and the user never touches it, the form submits "3" even though the user didn't intentionally rate that dimension.
**Why it happens:** HTML range inputs always have a value — there's no "empty" state for `<input type="range">`.
**How to avoid:** Don't set an initial `value` on flavor sliders. Instead:
1. Start with a "not rated" state — display "—" next to the slider.
2. Use a data attribute or hidden input that tracks whether the user interacted with the slider.
3. On the server side, only save flavor values for sliders that were explicitly touched.
**Implementation approach:**
```html
<input type="range" name="acidity" min="1" max="5" step="1"
       class="flavor-slider flavor-slider--unset"
       oninput="this.classList.remove('flavor-slider--unset'); this.nextElementSibling.textContent = this.value; this.dataset.touched = 'true'">
<span class="flavor-slider-value">—</span>
```
```python
# Server-side: only save if explicitly set
acidity_val = form.get("acidity")
acidity_touched = form.get("acidity_touched")  # or check via a convention
```
**Alternative simpler approach:** Use a checkbox or toggle per dimension to "enable" it before showing the slider. Or accept that sliders always send a value and use a separate "dirty" tracking hidden input per slider.
**Warning signs:** All shots having identical flavor profile values (all 3s).

### Pitfall 2: `<dialog>` Not Styled for Dark Theme
**What goes wrong:** The `<dialog>` element has default browser styling (white background, thin border) that clashes with the dark espresso theme.
**Why it happens:** `<dialog>` resets to browser defaults, ignoring parent CSS.
**How to avoid:** Explicitly style `dialog` and `dialog::backdrop` in main.css:
```css
dialog {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  max-width: 90vw;
  width: 480px;
  max-height: 85vh;
  overflow-y: auto;
}
dialog::backdrop {
  background: rgba(0, 0, 0, 0.6);
}
```
**Warning signs:** White flash when modal opens.

### Pitfall 3: htmx Request After Modal Opens — Timing
**What goes wrong:** `hx-on::after-swap` fires before the DOM is fully painted, causing `showModal()` to act on stale content.
**Why it happens:** htmx swap and browser paint are async.
**How to avoid:** Use `hx-on::after-settle` instead of `hx-on::after-swap` for the showModal call, since settle fires after htmx has finished processing:
```html
hx-on::after-settle="document.getElementById('shot-modal').showModal()"
```
**Warning signs:** Modal appears empty briefly, or content flickers.

### Pitfall 4: Tag Input Accessibility
**What goes wrong:** Custom tag input not keyboard-accessible; can't navigate suggestions with arrow keys.
**Why it happens:** Building autocomplete from scratch without considering keyboard navigation.
**How to avoid:** Keep the tag input simple:
- Use a standard text input with a `<datalist>` for suggestions (simplest approach).
- Or use a dropdown that appears below the input with keyboard arrow navigation.
- Ensure each tag can be removed via keyboard (Tab to tag, Enter/Delete to remove).
**Recommended approach:** Start with `<datalist>` which gives free autocomplete behavior:
```html
<input type="text" list="flavor-suggestions" id="tag-search"
       placeholder="Type flavor descriptor...">
<datalist id="flavor-suggestions">
  <option value="Chocolate">
  <option value="Berry">
  <option value="Citrus">
  <!-- ... -->
</datalist>
```
Then use minimal JS to: (1) on Enter/select, add to tag list, (2) prevent duplicates, (3) enforce max 10 limit, (4) update hidden input with JSON array.

### Pitfall 5: JSON Column Migration
**What goes wrong:** Adding a new `flavor_tags` JSON column requires an Alembic migration, and SQLite doesn't support all ALTER TABLE operations.
**Why it happens:** SQLite has limited ALTER TABLE support.
**How to avoid:** Use `batch_alter_table` context manager (already used in existing migrations):
```python
def upgrade() -> None:
    with op.batch_alter_table("measurements", schema=None) as batch_op:
        batch_op.add_column(sa.Column("flavor_tags", sa.JSON(), nullable=True))
```
**Warning signs:** Migration fails with "near ALTER: syntax error".

### Pitfall 6: Lost Form State on Modal Save
**What goes wrong:** After saving edits in the modal, the shot list behind it shows stale data.
**Why it happens:** Modal form submission updates the modal content but not the list row.
**How to avoid:** Use `hx-swap-oob` to update both the modal content and the corresponding list row in a single response:
```python
# In the save handler, return both updated modal + updated row
return HTMLResponse(
    content=render("history/_shot_modal.html", shot=shot) +
            render("history/_shot_row.html", shot=shot, oob=True)
)
```
```html
<!-- In _shot_row.html when oob=True -->
<div id="shot-{{ shot.id }}" hx-swap-oob="true" class="shot-row">
  ...
</div>
```

## Code Examples

### Example 1: History Router Structure
```python
# app/routers/history.py
"""Brew history — shot list, detail, filtering, editing."""

from typing import Optional
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.bean import Bean
from app.models.measurement import Measurement

router = APIRouter(prefix="/history", tags=["history"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def history_index(
    request: Request,
    bean_id: str = "",
    db: Session = Depends(get_db),
):
    """Full history page with filter sidebar and shot list."""
    beans = db.query(Bean).order_by(Bean.name).all()
    query = db.query(Measurement).order_by(Measurement.created_at.desc())
    if bean_id:
        query = query.filter(Measurement.bean_id == bean_id)
    shots = query.all()

    return templates.TemplateResponse(
        request,
        "history/index.html",
        {
            "beans": beans,
            "shots": shots,
            "selected_bean_id": bean_id,
        },
    )


@router.get("/shots", response_class=HTMLResponse)
async def shot_list_partial(
    request: Request,
    bean_id: str = "",
    min_taste: float = 1.0,
    db: Session = Depends(get_db),
):
    """Partial: filtered shot list for htmx swap."""
    query = db.query(Measurement).order_by(Measurement.created_at.desc())
    if bean_id:
        query = query.filter(Measurement.bean_id == bean_id)
    if min_taste > 1.0:
        query = query.filter(Measurement.taste >= min_taste)
    shots = query.all()

    return templates.TemplateResponse(
        request,
        "history/_shot_list.html",
        {"shots": shots},
    )


@router.get("/{shot_id}", response_class=HTMLResponse)
async def shot_detail(
    request: Request,
    shot_id: int,
    db: Session = Depends(get_db),
):
    """Partial: shot detail for modal content."""
    shot = db.query(Measurement).filter(Measurement.id == shot_id).first()
    if not shot:
        return HTMLResponse("<p>Shot not found</p>", status_code=404)
    return templates.TemplateResponse(
        request,
        "history/_shot_modal.html",
        {"shot": shot},
    )
```

### Example 2: Measurement Model Update
```python
# Add to app/models/measurement.py
from sqlalchemy import JSON

class Measurement(Base):
    # ... existing fields ...

    # Flavor tags (Phase 4 addition)
    flavor_tags = Column(JSON, nullable=True)  # ["chocolate", "berry", ...]
```

### Example 3: Alembic Migration for flavor_tags
```python
"""add flavor_tags to measurements

Revision ID: [auto-generated]
Revises: a2f1c3d5e7b9
"""
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    with op.batch_alter_table("measurements", schema=None) as batch_op:
        batch_op.add_column(sa.Column("flavor_tags", sa.JSON(), nullable=True))

def downgrade() -> None:
    with op.batch_alter_table("measurements", schema=None) as batch_op:
        batch_op.drop_column("flavor_tags")
```

### Example 4: `<dialog>` Modal CSS (Dark Theme)
```css
/* Shot detail modal */
.shot-modal {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 0;
  max-width: 90vw;
  width: 480px;
  max-height: 85vh;
  overflow-y: auto;
}

.shot-modal::backdrop {
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(2px);
}

.shot-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  background: var(--bg-card);
  z-index: 1;
}

.shot-modal-body {
  padding: var(--spacing-lg);
}
```

### Example 5: Flavor Slider CSS
```css
/* Flavor dimension sliders — smaller than taste slider */
.flavor-slider-row {
  display: grid;
  grid-template-columns: 80px 1fr 32px;
  align-items: center;
  gap: var(--spacing-sm);
  min-height: var(--touch-target);
}

.flavor-slider-label {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  font-weight: 500;
}

.flavor-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 6px;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 3px;
  outline: none;
  cursor: pointer;
}

.flavor-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
  border: 2px solid var(--bg-primary);
}

.flavor-slider::-moz-range-thumb {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
  border: 2px solid var(--bg-primary);
}

/* Unset state — dimmed slider before user interaction */
.flavor-slider--unset {
  opacity: 0.4;
}

.flavor-slider-value {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  text-align: center;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
```

### Example 6: Tag Input (Minimal JS)
```javascript
// Flavor tag input — vanilla JS, no library
(function() {
  const PREDEFINED_TAGS = [
    'Chocolate', 'Dark Chocolate', 'Cocoa', 'Caramel', 'Toffee', 'Brown Sugar',
    'Honey', 'Maple', 'Vanilla', 'Nutty', 'Almond', 'Hazelnut', 'Walnut',
    'Berry', 'Blueberry', 'Raspberry', 'Strawberry', 'Blackberry',
    'Citrus', 'Lemon', 'Orange', 'Grapefruit', 'Lime', 'Tangerine',
    'Stone Fruit', 'Peach', 'Apricot', 'Cherry', 'Plum',
    'Tropical', 'Mango', 'Pineapple', 'Passionfruit', 'Coconut',
    'Apple', 'Pear', 'Grape', 'Fig', 'Date', 'Raisin',
    'Floral', 'Jasmine', 'Rose', 'Lavender', 'Hibiscus',
    'Spicy', 'Cinnamon', 'Clove', 'Cardamom', 'Black Pepper', 'Ginger',
    'Earthy', 'Tobacco', 'Leather', 'Cedar', 'Woody', 'Smoky',
    'Roasty', 'Toasted', 'Burnt', 'Ashy',
    'Winey', 'Fermented', 'Whiskey', 'Brandy',
    'Buttery', 'Creamy', 'Silky', 'Syrupy',
    'Clean', 'Bright', 'Crisp', 'Juicy', 'Tea-like',
    'Savory', 'Umami', 'Salty', 'Malty',
    'Bitter', 'Astringent', 'Sour', 'Tannic', 'Dry'
  ];
  const MAX_TAGS = 10;
  let selectedTags = [];

  const searchInput = document.getElementById('tag-search');
  const tagList = document.getElementById('tag-list');
  const hiddenInput = document.getElementById('flavor-tags-hidden');
  const suggestionsDiv = document.getElementById('tag-suggestions');

  if (!searchInput) return; // not on this page

  function updateHidden() {
    hiddenInput.value = JSON.stringify(selectedTags);
  }

  function renderTags() {
    tagList.innerHTML = selectedTags.map(tag =>
      `<span class="tag-badge">${tag}
        <button type="button" class="tag-remove" onclick="removeTag('${tag}')">&times;</button>
      </span>`
    ).join('');
    updateHidden();
  }

  window.removeTag = function(tag) {
    selectedTags = selectedTags.filter(t => t !== tag);
    renderTags();
  };

  function addTag(tag) {
    tag = tag.trim();
    if (!tag || selectedTags.includes(tag) || selectedTags.length >= MAX_TAGS) return;
    selectedTags.push(tag);
    renderTags();
    searchInput.value = '';
    suggestionsDiv.style.display = 'none';
  }

  searchInput.addEventListener('input', function() {
    const query = this.value.toLowerCase().trim();
    if (query.length < 1) { suggestionsDiv.style.display = 'none'; return; }

    const matches = PREDEFINED_TAGS
      .filter(t => t.toLowerCase().includes(query) && !selectedTags.includes(t))
      .slice(0, 8);

    if (matches.length === 0) { suggestionsDiv.style.display = 'none'; return; }

    suggestionsDiv.innerHTML = matches.map(t =>
      `<div class="tag-suggestion" onclick="document.dispatchEvent(new CustomEvent('selectTag', {detail:'${t}'}))">${t}</div>`
    ).join('');
    suggestionsDiv.style.display = 'block';
  });

  document.addEventListener('selectTag', e => addTag(e.detail));

  searchInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTag(this.value);
    }
  });
})();
```

### Example 7: Navigation Link Addition
```html
<!-- In base.html nav-links, add History link -->
<div class="nav-links">
  <a href="/brew" class="nav-link">Brew</a>
  <a href="/history" class="nav-link">History</a>
</div>
```

### Example 8: Extending /brew/record to Accept New Fields
```python
@router.post("/record", response_class=HTMLResponse)
async def record_measurement(
    request: Request,
    # ... existing params ...
    notes: Optional[str] = Form(None),
    acidity: Optional[float] = Form(None),
    sweetness: Optional[float] = Form(None),
    body: Optional[float] = Form(None),
    bitterness: Optional[float] = Form(None),
    aroma: Optional[float] = Form(None),
    intensity: Optional[float] = Form(None),
    flavor_tags: Optional[str] = Form(None),  # JSON string
    db: Session = Depends(get_db),
):
    # ... existing logic ...
    if not existing:
        # Parse flavor tags from JSON string
        tags = None
        if flavor_tags:
            import json
            try:
                tags = json.loads(flavor_tags)
                if not isinstance(tags, list):
                    tags = None
            except json.JSONDecodeError:
                tags = None

        measurement = Measurement(
            # ... existing fields ...
            notes=notes.strip() if notes else None,
            acidity=acidity,
            sweetness=sweetness,
            body=body,
            bitterness=bitterness,
            aroma=aroma,
            intensity=intensity,
            flavor_tags=tags,
        )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom modal overlays with JS focus trap | HTML `<dialog>` with `showModal()` | Widely available since March 2022 | No JS library needed for accessible modals |
| `<details>`/`<summary>` for expandable panels | Still valid, but project uses custom CSS toggle | N/A | Keep using existing pattern for consistency |
| Separate DB table for tags (junction table) | JSON columns in SQLite (JSON1 extension) | SQLite 3.38+ (2022) built-in | Simpler schema, still queryable with `json_each()` |
| htmx Hyperscript for modal close | Vanilla JS event listeners | Ongoing | No need for Hyperscript dependency |

**Deprecated/outdated:**
- Nothing deprecated relevant to this phase. htmx 2.0.4 is current.

## Flavor Descriptor Tag List (Predefined)

Based on SCA (Specialty Coffee Association) flavor wheel and common cupping descriptors:

**Fruity:** Berry, Blueberry, Raspberry, Strawberry, Blackberry, Citrus, Lemon, Orange, Grapefruit, Stone Fruit, Peach, Apricot, Cherry, Plum, Tropical, Mango, Pineapple, Passionfruit, Apple, Pear, Grape, Fig, Date, Raisin

**Sweet:** Chocolate, Dark Chocolate, Cocoa, Caramel, Toffee, Brown Sugar, Honey, Maple, Vanilla

**Nutty:** Nutty, Almond, Hazelnut, Walnut

**Floral:** Floral, Jasmine, Rose, Lavender, Hibiscus

**Spicy:** Spicy, Cinnamon, Clove, Cardamom, Black Pepper, Ginger

**Earthy/Roasty:** Earthy, Tobacco, Leather, Cedar, Woody, Smoky, Roasty, Toasted

**Body/Texture:** Buttery, Creamy, Silky, Syrupy, Clean, Bright, Crisp, Juicy, Tea-like, Dry

**Other:** Winey, Fermented, Savory, Umami, Malty, Bitter, Astringent, Sour, Tannic

Total: ~80 predefined tags. Users can also enter custom tags not in this list.

## Open Questions

1. **Slider "unset" state UX:**
   - What we know: HTML range inputs always have a value; there's no native "empty" state.
   - What's unclear: Best UX pattern for "optional but has a slider" — checkbox per dimension? Dimmed slider? Separate enable toggle?
   - Recommendation: Use dimmed slider (opacity 0.4) with "—" value display. First touch activates it and removes the dimmed class. Server treats untouched sliders as null. Track "touched" state via a data attribute and a hidden input per slider.

2. **Filter panel responsive behavior:**
   - Decision says: collapsed behind "Filter" button on mobile, always-open side panel on wider viewports.
   - What's unclear: Exact breakpoint. Current container max-width is 480px (540px on wider).
   - Recommendation: Use a CSS media query at `min-width: 768px` to show filter as a side panel. Below that, show it as a collapsible section above the list using the existing `.collapsible-toggle` pattern.

3. **Bean relationship in shot list:**
   - What we know: Need to show bean name in the global history list.
   - What's unclear: Whether to eager-load beans or join.
   - Recommendation: Use `joinedload(Measurement.bean)` in the history query to avoid N+1 queries. The relationship already exists in the model (`bean = relationship("Bean", ...)`).

## Sources

### Primary (HIGH confidence)
- **Codebase analysis** — `app/models/measurement.py`, `app/routers/brew.py`, `app/templates/`, `app/static/css/main.css` — all patterns directly observed
- **htmx.org official docs** — Modal examples, active search, hx-trigger, hx-swap-oob, HX-Trigger headers
- **MDN `<dialog>` docs** — https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog — native dialog behavior, accessibility, styling

### Secondary (MEDIUM confidence)
- **SCA Flavor Wheel** — basis for predefined flavor tag list (well-established industry standard)
- **SQLite JSON1 docs** — JSON column support in SQLite (built-in since 3.38)

### Tertiary (LOW confidence)
- None — all findings verified with primary or secondary sources.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies, all verified in existing codebase
- Architecture: HIGH — patterns directly from htmx docs + existing codebase conventions
- DB schema: HIGH — JSON column already used in project (Bean.parameter_overrides), adding another is consistent
- Pitfalls: HIGH — based on direct analysis of existing code patterns and known HTML/htmx behaviors
- Tag list: MEDIUM — based on SCA standards but exact selection is discretionary

**Research date:** 2026-02-22
**Valid until:** 2026-04-22 (stable stack, no fast-moving dependencies)
