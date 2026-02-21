# Architecture Patterns

**Domain:** Phone-first espresso optimization webapp with BayBE
**Researched:** 2026-02-21

## Recommended Architecture

### Overview

BrewFlow is a **monolithic server-rendered webapp** with a Python backend serving HTML via Jinja2 templates, enhanced with htmx for dynamic interactions. The BayBE optimization engine runs in-process. Data is stored in SQLite. The entire application is a single Docker container.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Container                         │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Uvicorn (ASGI Server)                  │   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐    │   │
│  │  │               FastAPI Application                 │    │   │
│  │  │                                                   │    │   │
│  │  │  ┌─────────┐  ┌───────────┐  ┌───────────────┐  │    │   │
│  │  │  │  Routes  │  │ Templates │  │  Static Files  │  │    │   │
│  │  │  │ (API +   │  │ (Jinja2)  │  │ (htmx, CSS,   │  │    │   │
│  │  │  │  Pages)  │  │           │  │  Chart.js)     │  │    │   │
│  │  │  └────┬─────┘  └───────────┘  └───────────────┘  │    │   │
│  │  │       │                                           │    │   │
│  │  │  ┌────┴─────────────────────────────────────┐     │    │   │
│  │  │  │            Service Layer                  │     │    │   │
│  │  │  │                                           │     │    │   │
│  │  │  │  ┌──────────────┐  ┌──────────────────┐  │     │    │   │
│  │  │  │  │  Bean Service │  │ Optimizer Service │  │     │    │   │
│  │  │  │  │  (CRUD ops)   │  │ (BayBE wrapper)  │  │     │    │   │
│  │  │  │  └──────┬────────┘  └────────┬─────────┘  │     │    │   │
│  │  │  └─────────┼────────────────────┼────────────┘     │    │   │
│  │  │            │                    │                   │    │   │
│  │  │  ┌─────────┴────────────────────┴────────────┐     │    │   │
│  │  │  │              Data Layer                    │     │    │   │
│  │  │  │                                            │     │    │   │
│  │  │  │  ┌──────────────┐  ┌───────────────────┐  │     │    │   │
│  │  │  │  │   SQLAlchemy  │  │  Campaign Store   │  │     │    │   │
│  │  │  │  │   (Models +   │  │  (BayBE JSON      │  │     │    │   │
│  │  │  │  │    Queries)   │  │   serialization)  │  │     │    │   │
│  │  │  │  └──────┬────────┘  └────────┬──────────┘  │     │    │   │
│  │  │  └─────────┼────────────────────┼─────────────┘     │    │   │
│  │  └────────────┼────────────────────┼──────────────────┘    │   │
│  └───────────────┼────────────────────┼───────────────────────┘   │
│                  │                    │                            │
│  ┌───────────────┴──┐  ┌─────────────┴──────────┐                │
│  │  SQLite Database  │  │  Campaign JSON Files   │                │
│  │  (measurements,   │  │  (BayBE state,         │                │
│  │   beans, metadata)│  │   /data/campaigns/)    │                │
│  └──────────────────┘  └────────────────────────┘                │
│                                                                   │
│  Volume mount: /data/ → Unraid persistent storage                │
└───────────────────────────────────────────────────────────────────┘
```

### Why This Architecture

1. **Monolith over microservices.** Single-user personal tool. One container to deploy. No inter-service communication overhead.

2. **Server-rendered over SPA.** Phone-first means fast initial load matters. Server-rendered HTML arrives painted. No JS framework hydration delay. htmx adds interactivity where needed.

3. **Dual storage (SQLite + JSON files).** SQLite stores everything queryable (beans, measurements, metadata). BayBE campaign state stays as JSON files because that's BayBE's native serialization format. Measurements in SQLite are the source of truth — campaigns can always be rebuilt from them.

4. **In-process BayBE.** No separate optimization service. BayBE runs in the same Python process. For single-user, this is the simplest and fastest option.

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **Routes (Pages)** | HTTP endpoints returning HTML pages (Jinja2 templates). Handles form submissions. | Service Layer, Templates |
| **Routes (API)** | JSON endpoints for htmx partial updates and AJAX calls (e.g., recommendation polling). | Service Layer |
| **Templates** | Jinja2 HTML templates. Phone-first layout. Includes htmx attributes for dynamic behavior. | Routes (rendered by) |
| **Static Files** | htmx.min.js, chart.js, app.css. Vendored or CDN. | Browser (served directly) |
| **Bean Service** | CRUD operations for beans. Creates/loads/lists beans. Manages the bean→campaign lifecycle. | Data Layer (SQLAlchemy), Campaign Store |
| **Optimizer Service** | Wraps BayBE: create campaigns, get recommendations, add measurements. Handles campaign caching, async recommend, continuous→discrete rounding. | Campaign Store, Data Layer |
| **Data Layer (SQLAlchemy)** | ORM models for beans, measurements, flavor profiles. Queries. Migration management. | SQLite Database |
| **Campaign Store** | Loads/saves BayBE campaign JSON files. In-memory cache. Campaign rebuild from measurements. | Campaign JSON Files, BayBE library |

### Data Flow

#### Core Loop: Recommend → Brew → Rate

```
1. User opens app on phone
   Browser → GET /beans/{id} → Routes → Bean Service → SQLAlchemy → SQLite
   Routes → Jinja2 template → HTML response with bean info + "Get Recommendation" button

2. User taps "Get Recommendation"
   Browser → POST /beans/{id}/recommend (htmx) → Routes → Optimizer Service
   Optimizer Service → Campaign Store (load from cache or JSON file)
   Optimizer Service → campaign.recommend(batch_size=1) [async, 3-10s]
   Optimizer Service → Routes → Jinja2 partial template → HTML fragment
   htmx swaps recommendation into the page

3. User brews, then taps "Rate This Shot"
   Browser → POST /beans/{id}/measurements (htmx, form data) → Routes
   Routes → validates with Pydantic model
   Routes → Optimizer Service → campaign.add_measurements(df)
   Routes → Bean Service → save measurement to SQLite
   Optimizer Service → Campaign Store (save updated campaign JSON)
   Routes → Jinja2 partial → HTML confirmation + "Get Next Recommendation" button
   htmx swaps confirmation into the page
```

#### Recommendation Async Pattern

```
Option A: Simple async (recommended for v1)
──────────────────────────────────────────────
POST /beans/{id}/recommend
  → asyncio.to_thread(campaign.recommend, batch_size=1)
  → Returns HTML fragment when complete
  → htmx shows loading indicator during wait (hx-indicator)
  → Timeout: 30s (more than enough for any recommendation)

Option B: Polling pattern (if Option A feels too slow for UX)
───────────────────────────────────────────────────────────────
POST /beans/{id}/recommend → Returns 202 + job_id immediately
  → Server starts recommendation in background thread
GET /beans/{id}/recommend/{job_id} → Returns 200 + HTML when ready, 202 while pending
  → htmx polls every 1s until 200 (hx-trigger="every 1s")
```

**Recommendation:** Start with Option A. htmx's `hx-indicator` shows a spinner. If 3-10 seconds feels acceptable (user is at their espresso machine, grinding coffee anyway), no need for polling complexity.

## Key Architecture Patterns

### Pattern 1: Measurements as Source of Truth

**What:** Store all measurement data in SQLite. BayBE campaign JSON files are a cache/optimization artifact, not the source of truth.

**When:** Always. This is the foundational pattern.

**Why:** Campaign JSON files are fragile (version-sensitive pickled objects, 20MB each). Measurements are simple rows of numbers. If a campaign file is corrupted or incompatible after a BayBE upgrade, rebuild it by replaying measurements.

**Implementation:**
```python
# Service layer
class OptimizerService:
    async def rebuild_campaign(self, bean_id: str) -> Campaign:
        """Disaster recovery: rebuild campaign from measurements."""
        campaign = create_fresh_campaign()
        measurements = await self.db.get_measurements(bean_id)
        if not measurements.empty:
            # Replay all historical measurements
            campaign.add_measurements(measurements[BAYBE_COLUMNS])
        self.campaign_store.save(bean_id, campaign)
        return campaign
```

### Pattern 2: Campaign In-Memory Cache

**What:** Load campaign objects into memory on first access, keep them cached for the server's lifetime, save to disk only on mutation.

**When:** Every campaign access.

**Why:** Campaign JSON files are 20MB. Loading from disk takes 1-3 seconds. Keeping them in memory eliminates this overhead for subsequent requests.

**Implementation:**
```python
class CampaignStore:
    def __init__(self, data_dir: Path):
        self._cache: dict[str, Campaign] = {}
        self._data_dir = data_dir
    
    def get(self, bean_id: str) -> Campaign:
        if bean_id not in self._cache:
            path = self._data_dir / f"{bean_id}.json"
            if path.exists():
                self._cache[bean_id] = Campaign.from_json(path.read_text())
            else:
                self._cache[bean_id] = create_fresh_campaign()
        return self._cache[bean_id]
    
    def save(self, bean_id: str, campaign: Campaign):
        self._cache[bean_id] = campaign
        path = self._data_dir / f"{bean_id}.json"
        path.write_text(campaign.to_json())
```

### Pattern 3: htmx Partial Rendering

**What:** Routes return either full HTML pages (direct navigation) or HTML fragments (htmx AJAX requests). Same template logic, different wrapping.

**When:** Any interactive UI element.

**Why:** htmx sends requests and swaps HTML fragments. The server detects htmx requests via the `HX-Request` header and returns just the fragment instead of a full page.

**Implementation:**
```python
@router.post("/beans/{bean_id}/recommend")
async def get_recommendation(
    request: Request,
    bean_id: str,
    optimizer: OptimizerService = Depends(get_optimizer),
):
    recommendation = await optimizer.recommend(bean_id)
    template = "partials/recommendation.html"  # Just the recommendation card
    
    if not request.headers.get("HX-Request"):
        template = "pages/bean.html"  # Full page with recommendation
    
    return templates.TemplateResponse(template, {
        "request": request,
        "recommendation": recommendation,
    })
```

### Pattern 4: Idempotent Measurement Submission

**What:** Each recommendation gets a unique ID. Submitting a measurement requires the recommendation ID. Duplicate submissions with the same ID are rejected.

**When:** Every measurement submission.

**Why:** Phone users with wet hands will double-tap. Network latency causes re-submissions. Without idempotency, duplicate measurements corrupt the optimization model.

**Implementation:**
```python
@router.post("/beans/{bean_id}/measurements")
async def submit_measurement(
    bean_id: str,
    measurement: MeasurementCreate,  # includes recommendation_id
    db: Session = Depends(get_db),
):
    # Check if this recommendation was already rated
    existing = db.query(Measurement).filter_by(
        recommendation_id=measurement.recommendation_id
    ).first()
    if existing:
        return templates.TemplateResponse("partials/already_submitted.html", {...})
    
    # Process normally
    ...
```

### Pattern 5: Progressive Enhancement for Charts

**What:** Charts are rendered client-side with Chart.js, but the page is functional without JavaScript. Data is passed to Chart.js via `<script>` tags with JSON data embedded in the template.

**When:** Any visualization page.

**Why:** The core recommend→rate loop doesn't need charts. Charts are for the "coffee analysis" sessions (usually on laptop). By passing data via template-embedded JSON, no separate API endpoint is needed.

**Implementation:**
```html
<!-- Jinja2 template -->
<div id="progress-chart">
    <canvas id="progressCanvas"></canvas>
</div>

<script>
    const chartData = {{ chart_data | tojson }};
    new Chart(document.getElementById('progressCanvas'), {
        type: 'line',
        data: chartData,
        options: { responsive: true, maintainAspectRatio: false }
    });
</script>

<!-- Fallback for no-JS (shouldn't happen but defensive) -->
<noscript>
    <p>Charts require JavaScript. Your data is still accessible in the history table above.</p>
</noscript>
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: BayBE Campaign as Source of Truth

**What:** Treating `campaign.to_json()` as the only record of optimization history.

**Why bad:** Campaign JSON files contain pickled objects that break across versions. If the file is corrupted or BayBE is upgraded, ALL history for that bean is lost. The 20MB files also can't be queried, browsed, or exported.

**Instead:** Store every measurement in SQLite with full metadata. Campaign JSON is a performance optimization that can always be regenerated from measurements.

### Anti-Pattern 2: Synchronous BayBE in Request Handler

**What:** Calling `campaign.recommend()` directly in a sync FastAPI endpoint, blocking the server.

**Why bad:** `recommend()` takes 3-10 seconds on CPU. During this time, the single-threaded event loop is blocked. No other requests can be served. User sees no feedback on their phone.

**Instead:** Use `asyncio.to_thread()` to run BayBE in a thread pool. Add `hx-indicator` to show a spinner in the UI.

### Anti-Pattern 3: Server-Side Chart Rendering (matplotlib)

**What:** Generating PNG/SVG charts on the server with matplotlib, sending images to the client.

**Why bad:** Heavy CPU usage per request. Static images aren't interactive (can't tap data points). Terrible on mobile (fixed aspect ratios, tiny text). matplotlib isn't designed for dynamic web charting.

**Instead:** Pass data as JSON to Chart.js, render client-side. Charts are responsive, interactive, and zero server CPU.

### Anti-Pattern 4: Separate Frontend/Backend Repos

**What:** React/Vue frontend in one repo, FastAPI backend in another, communicating via JSON API.

**Why bad:** For a 5-screen personal tool, this doubles the codebase, requires two build systems, adds API contract management, and means context-switching between two languages. No team to distribute work across.

**Instead:** Single repo, Jinja2 templates live alongside Python code. One `docker build`, one deployment.

### Anti-Pattern 5: Over-Engineering the Data Model

**What:** Creating normalized tables for every concept (separate tables for flavor profiles, parameters, tags, categories, etc.) before validating that they're needed.

**Why bad:** This is a personal espresso tool. The data model is simple: beans and measurements. Over-normalizing adds migration complexity, join queries, and conceptual overhead for zero benefit.

**Instead:** Start with two tables (beans, measurements). Flavor profile fields are columns on measurements. Add tables only when a real need arises.

## Project Structure

```
brewflow/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app creation, lifespan, middleware
│   ├── config.py             # Settings (pydantic-settings)
│   ├── database.py           # SQLAlchemy engine, session factory
│   ├── models/
│   │   ├── __init__.py
│   │   ├── bean.py           # SQLAlchemy: Bean model
│   │   └── measurement.py    # SQLAlchemy: Measurement model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── bean.py           # Pydantic: Bean request/response schemas
│   │   └── measurement.py    # Pydantic: Measurement schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── bean_service.py   # Bean CRUD operations
│   │   └── optimizer.py      # BayBE wrapper: recommend, add_measurements, rebuild
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── pages.py          # Full page routes (GET /beans, GET /beans/{id})
│   │   └── api.py            # htmx partial routes (POST /recommend, POST /measure)
│   ├── templates/
│   │   ├── base.html         # Base template (head, nav, footer)
│   │   ├── pages/
│   │   │   ├── home.html     # Bean list / landing page
│   │   │   ├── bean.html     # Bean detail: recommendation + feedback + history
│   │   │   └── stats.html    # Statistics / cross-bean dashboard
│   │   └── partials/
│   │       ├── recommendation.html   # Recommendation card (htmx fragment)
│   │       ├── feedback_form.html    # Rating form (htmx fragment)
│   │       ├── confirmation.html     # Post-submission confirmation
│   │       ├── history_table.html    # Shot history table
│   │       └── charts.html           # Chart containers + Chart.js init
│   └── static/
│       ├── css/
│       │   └── app.css        # All styles (~200 lines)
│       └── js/
│           ├── htmx.min.js    # Vendored htmx (16KB gzipped)
│           └── chart.min.js   # Vendored Chart.js
├── data/                      # Docker volume mount point
│   ├── brewflow.db            # SQLite database
│   └── campaigns/             # BayBE campaign JSON files
├── migrations/                # Alembic migration scripts
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
├── tests/
│   ├── conftest.py
│   ├── test_routes.py
│   ├── test_optimizer.py
│   └── test_models.py
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Scalability Considerations

| Concern | At 1 user (v1) | At 5 users (v2 maybe) | At 100+ users (unlikely) |
|---------|----------------|----------------------|--------------------------|
| **Database** | SQLite, single file, trivial | SQLite still fine (serialized writes, but writes are rare) | PostgreSQL migration needed |
| **Campaign storage** | In-memory cache, JSON files on disk | Separate campaigns per user, memory grows | Need campaign-as-a-service or shared campaigns |
| **Recommendation latency** | 3-10s acceptable (single user waits) | Multiple users might queue; still OK with thread pool | Need dedicated recommendation workers |
| **Docker** | Single container | Single container still fine | Multiple containers, load balancer |
| **Auth** | None needed | Simple auth (basic or session-based) | Full auth system (OAuth, JWT) |

**BrewFlow is designed for 1 user. Multi-user is a v2+ concern.** The architecture supports it (user_id in data model, service layer abstraction) but doesn't implement it.

## Sources

- **FastAPI architecture patterns** — https://fastapi.tiangolo.com/tutorial/bigger-applications/ (project structure, routers, dependency injection). Confidence: HIGH.
- **htmx patterns** — https://htmx.org/ (partial rendering, hx-indicator, hx-swap). Confidence: HIGH.
- **SQLite server-side pattern** — https://sqlite.org/whentouse.html#server_side_database ("separate SQLite database for each user" pattern). Confidence: HIGH.
- **BayBE serialization** — Existing codebase analysis (`my_espresso.py`, campaign JSON files). Confidence: HIGH.
- **Existing Marimo app** — `my_espresso.py` (641 lines) analysis for current architecture patterns. Confidence: HIGH.

---
*Architecture research for: BrewFlow — Phone-first espresso optimization webapp with BayBE*
*Researched: 2026-02-21*
