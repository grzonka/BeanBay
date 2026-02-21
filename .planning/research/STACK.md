# Technology Stack

**Project:** BrewFlow — Phone-first espresso optimization webapp
**Researched:** 2026-02-21

## Recommended Stack

### Core Backend

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Python** | 3.11+ | Runtime | BayBE requires Python. 3.11 for performance improvements and better error messages. 3.12+ may work but needs BayBE compatibility testing. |
| **FastAPI** | latest (0.115+) | Web framework / API | Async-native (critical for BayBE's slow `recommend()` calls), Pydantic integration for request/response validation, auto-generated OpenAPI docs, built-in BackgroundTasks for async operations. The standard Python API framework. |
| **Uvicorn** | latest | ASGI server | FastAPI's recommended server. Handles async requests efficiently. Single-worker is fine for single-user. |
| **BayBE** | 0.14.2 (pinned) | Bayesian optimization | Project constraint. Already proven in existing Marimo app. Pin exact version to avoid serialization breakage. |
| **Pydantic** | v2 (via FastAPI) | Data validation & serialization | FastAPI dependency. Use for all API models, configuration, and data validation. |

### Database

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **SQLite** | 3.x (stdlib) | Primary data store | Perfect fit: single-user, local, zero-config, built into Python stdlib, handles concurrent reads, atomic writes. No need for PostgreSQL/MySQL for a single-user homeserver app. SQLite is explicitly designed for this exact use case ("application file format", "server-side database with serialized writes"). |
| **SQLAlchemy** | 2.0+ | ORM / query builder | Industry standard Python ORM. Provides migrations via Alembic, type-safe queries, connection pooling. Works beautifully with SQLite and FastAPI. |
| **Alembic** | 1.18+ | Database migrations | SQLAlchemy's migration tool. Handles schema evolution as features are added. Has specific SQLite batch migration support for ALTER TABLE limitations. |

### Frontend

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Jinja2** | 3.1+ | Server-side HTML templating | FastAPI has built-in Jinja2 support. Server-rendered HTML means no build step, no Node.js toolchain, no SPA complexity. Pages load fast because they're complete HTML from the server. |
| **htmx** | 2.0+ | Dynamic UI interactions | Provides AJAX, partial page updates, and interactive UI without writing JavaScript. Perfect for the recommend→rate→repeat workflow. Button click → server returns HTML fragment → htmx swaps it in. No React/Vue/Svelte needed. |
| **Chart.js** | 4.x | Client-side charting | Most popular JS charting library (~60k GitHub stars). Renders on Canvas (performant), responsive by default, mobile-friendly, works with vanilla JS. No npm/webpack needed — load from CDN. Built-in line charts, scatter plots, and bar charts cover all BrewFlow visualization needs. |
| **CSS (vanilla + custom properties)** | — | Styling | No CSS framework needed for a focused single-purpose app. Use CSS custom properties for theming (light/dark), CSS Grid/Flexbox for layout. Avoids Tailwind/Bootstrap build complexity. A simple ~200-line CSS file handles everything. |

### Infrastructure

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Docker** | — | Containerization | Project constraint (Unraid deployment). Single-container deployment with volume mounts for data persistence. |
| **Docker Compose** | — | Container orchestration | Simple `docker-compose.yml` for defining the service, volumes, ports, and environment variables. Standard for Unraid. |

### Development & Testing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **pytest** | 8+ | Testing framework | Standard Python testing. FastAPI has excellent pytest integration via `TestClient`. |
| **httpx** | — | Test client | FastAPI's recommended test client (via `TestClient`). Async-capable. |
| **Ruff** | latest | Linting + formatting | Already in use (`.ruff_cache/` exists). Replaces flake8/isort/black in a single fast tool. |
| **uv** | latest | Package management | Fastest Python package installer. Creates lockfiles for reproducible builds. Handles virtual environments. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **pandas** | 2.x | DataFrames | BayBE interface — measurements are ingested as DataFrames. Also useful for data export/analysis. |
| **numpy** | 1.26+ | Numeric arrays | BayBE dependency. Pin version to match BayBE's requirements for serialization compatibility. |
| **torch** (CPU-only) | 2.x | ML backend | BayBE/BoTorch dependency. Install CPU-only variant to save ~1GB in Docker image. |
| **pydantic-settings** | 2.x | Configuration | Environment-based config (database path, server port, log level). Clean `.env` file support. |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| **Web Framework** | FastAPI | Flask | Flask lacks native async support. BayBE's `recommend()` blocks for 3-10s — async is essential, not optional. FastAPI is the modern standard for Python APIs. |
| **Web Framework** | FastAPI | Django | Massive overkill for a single-user personal tool. Django's ORM, admin, auth system are unnecessary weight. Django's async story is still catching up. |
| **Web Framework** | FastAPI | Litestar | Newer, less ecosystem/community support. FastAPI is the safe, well-documented choice. |
| **Frontend** | htmx + Jinja2 | React/Next.js | Requires Node.js build toolchain, separate frontend/backend repos, API contract management. Massively over-engineered for a personal tool with ~5 screens. Adds 500KB+ of JS to the client. BayBE is already Python — keep everything in one language. |
| **Frontend** | htmx + Jinja2 | Svelte/SvelteKit | Same Node.js toolchain objection as React. Svelte is elegant but unnecessary for this app's complexity level. |
| **Frontend** | htmx + Jinja2 | Streamlit | No control over UI/UX. Terrible on mobile. Not designed for phone-first interactions. Would repeat the same problems as Marimo. |
| **Frontend** | htmx + Jinja2 | Gradio | Same problems as Streamlit — designed for ML demos, not production phone UIs. |
| **Frontend** | htmx + Jinja2 | Alpine.js + fetch | Alpine.js is a valid alternative to htmx. htmx is preferred because it requires zero JavaScript — interactions are declared in HTML attributes, which is simpler for a Python developer to maintain. |
| **Database** | SQLite | PostgreSQL | Requires separate container, connection management, configuration. Complete overkill for single-user with <100 rows per bean. SQLite handles the expected load trivially. |
| **Database** | SQLite | JSON/CSV files | Current approach — has corruption risk, no query capability, no schema enforcement. See PITFALLS.md #9. SQLite is strictly better. |
| **ORM** | SQLAlchemy | Raw sqlite3 | Works but no migrations, no type safety, manual SQL strings. SQLAlchemy provides a clean abstraction with minimal overhead. |
| **ORM** | SQLAlchemy | Tortoise ORM | Less mature, smaller ecosystem. SQLAlchemy is the standard. |
| **Charting** | Chart.js | Plotly.js | 3MB+ bundle size vs Chart.js's ~200KB. Plotly's interactivity features are overkill. Chart.js covers line, scatter, and bar charts needed. |
| **Charting** | Chart.js | Matplotlib (server-side) | Current approach — generates static images, no interactivity, terrible on mobile, heavy CPU usage per render. Client-side charting is strictly better for a webapp. |
| **Charting** | Chart.js | D3.js | Too low-level. Chart.js provides high-level chart types out of the box. D3 requires writing significant code for basic charts. |
| **Package Manager** | uv | pip + pip-tools | uv is 10-100x faster, handles lockfiles natively, replaces virtualenv/pip/pip-tools in one tool. The Python ecosystem has converged on uv. |

## Key Stack Decisions

### Why htmx + Jinja2 Instead of a JavaScript Framework

This is the most important stack decision. The arguments for htmx:

1. **No build step.** No webpack, no Vite, no `node_modules`, no `package.json`. HTML templates are just files. This drastically simplifies development and Docker builds.

2. **One language.** The entire app is Python. Templates are Jinja2 (Python-like syntax). No context-switching between Python and TypeScript.

3. **Phone-first works better with server rendering.** HTML arrives complete and painted immediately. No JavaScript hydration delay. On a phone over WiFi to a local server, the round-trip is <10ms — faster than any client-side framework's initial render.

4. **htmx handles the interaction pattern perfectly.** BrewFlow's core loop is: click "Get Recommendation" → server runs BayBE → return HTML with recipe → user brews → click "Rate" → submit form → server records → return confirmation. This is the exact pattern htmx was designed for.

5. **~5 screens total.** The UI has: bean list, recommendation view, feedback form, history/charts, settings. A JS framework adds architectural complexity that pays off at 50+ screens, not 5.

6. **Docker image stays small.** No Node.js runtime needed in the container.

### Why SQLite Instead of "Just Files"

The existing app uses JSON + CSV files. SQLite is better because:

1. **Atomic writes.** No corruption from interrupted writes (PITFALLS #9).
2. **Queryable.** "Show me all shots where taste > 7 sorted by date" is a SQL query, not a pandas pipeline.
3. **Schema enforcement.** Columns have types. Missing fields are caught at insert time.
4. **Migrations.** Alembic can evolve the schema as features are added.
5. **Zero config.** SQLite is built into Python. No server to run.
6. **Future-proof.** If multi-user is ever needed, the data model already exists — just add a user_id column.

### Why FastAPI's BackgroundTasks Instead of Celery/Redis

BayBE's `recommend()` takes 3-10 seconds. Options for handling this:

1. **Celery + Redis** — Full task queue. Massive overkill for a single-user app. Two extra containers.
2. **FastAPI BackgroundTasks** — Built-in, simple. Start recommendation in background, client polls for result.
3. **Simple threading** — Python's `threading.Thread` or `asyncio.to_thread()` wraps the blocking BayBE call.

**Recommendation:** Use `asyncio.to_thread()` to run BayBE in a thread pool, returning results via the async endpoint. If that proves insufficient, upgrade to BackgroundTasks with a polling endpoint. No need for Celery.

## Installation

```bash
# Create virtual environment with uv
uv venv
source .venv/bin/activate

# Core dependencies
uv pip install "fastapi[standard]" sqlalchemy alembic pydantic-settings

# BayBE (CPU-only PyTorch first to avoid CUDA download)
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
uv pip install baybe==0.14.2

# Data/science (BayBE dependencies, but pin explicitly)
uv pip install pandas numpy

# Frontend (no install needed — htmx and Chart.js loaded from CDN or vendored)
# Jinja2 comes with FastAPI[standard]

# Development
uv pip install pytest httpx ruff
```

```bash
# Docker: CPU-only PyTorch installation
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install baybe==0.14.2
# This saves ~1GB compared to default torch install
```

## Version Pinning Strategy

**Critical pins** (serialization-sensitive — BayBE campaign files depend on these):
- `baybe==0.14.2`
- `numpy` — pin to whatever BayBE 0.14.2 resolves to
- `pandas` — pin to whatever BayBE 0.14.2 resolves to
- `torch` — pin to whatever BayBE 0.14.2 resolves to

**Flexible pins** (can update freely):
- `fastapi`, `uvicorn`, `sqlalchemy`, `alembic` — use `>=` with reasonable floor
- `jinja2`, `pydantic` — come with FastAPI
- `chart.js`, `htmx` — CDN or vendored, version in HTML

**Use `uv pip compile`** to generate a lockfile for reproducible Docker builds.

## Sources

- **FastAPI** — https://fastapi.tiangolo.com/ (official docs, confirmed current as of Feb 2026). Confidence: HIGH.
- **htmx** — https://htmx.org/ (v2.0.8 confirmed current). 16k min+gzip, no dependencies. Confidence: HIGH.
- **SQLite** — https://sqlite.org/whentouse.html (official docs on when to use SQLite). Confirms SQLite is ideal for "server-side database" with serialized writes, embedded applications. Confidence: HIGH.
- **Chart.js** — https://www.chartjs.org/docs/latest/ (v4.x, ~60k GitHub stars, Canvas rendering, responsive). Confidence: HIGH.
- **Alembic** — https://alembic.sqlalchemy.org/en/latest/ (v1.18+, has SQLite batch migration support). Confidence: HIGH.
- **Pydantic** — https://docs.pydantic.dev/latest/ (v2.12.5, FastAPI's data validation layer). Confidence: HIGH.
- **Jinja2** — https://jinja.palletsprojects.com/en/stable/ (v3.1.x, FastAPI built-in support). Confidence: HIGH.
- **BayBE** — existing codebase (`my_espresso.py`, `requirements.txt`). Version 0.14.2 confirmed. Confidence: HIGH.

---
*Stack research for: BrewFlow — Phone-first espresso optimization webapp with BayBE*
*Researched: 2026-02-21*
