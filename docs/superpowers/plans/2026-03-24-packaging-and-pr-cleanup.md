# Packaging, CLI & PR Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package BeanBay as a single installable Python package with bundled React frontend, CLI entrypoint, Dockerfile, and cleaned-up tooling — ready for PR into main.

**Architecture:** Hatch custom build hook builds the Vite frontend into `src/beanbay/static/` during wheel creation. FastAPI serves these files alongside the API. A `beanbay` CLI entrypoint starts the app. Three-stage Dockerfile separates bun, Python, and runtime concerns.

**Tech Stack:** Hatchling, Vite, bun, FastAPI StaticFiles, uvicorn, Biome, ruff, pre-commit, Docker multi-stage

**Spec:** `docs/superpowers/specs/2026-03-24-packaging-and-pr-cleanup-design.md`

---

### Task 1: Remove Alembic Migrations and Switch to create_all

**Files:**
- Delete: `migrations/versions/080ccd3b160a_add_person_id_and_optimization_mode_to_.py`
- Delete: `migrations/versions/64a82453ad53_initial_schema_tz_aware.py`
- Modify: `src/beanbay/main.py:1-63`
- Modify: `pyproject.toml:7-17,44-47`

- [ ] **Step 1: Delete migration version files**

Do NOT delete `migrations/env.py`, `migrations/script.py.mako`, or `alembic.ini` —
these are retained for future migration authoring.

```bash
rm migrations/versions/080ccd3b160a_add_person_id_and_optimization_mode_to_.py
rm migrations/versions/64a82453ad53_initial_schema_tz_aware.py
```

- [ ] **Step 2: Update lifespan handler in main.py**

Replace the Alembic upgrade call with `SQLModel.metadata.create_all`. Remove
Alembic imports. The file is `src/beanbay/main.py`.

Replace lines 30-62 (the lifespan function) with:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Creates database tables, seeds default lookup data and the default
    person record.  Starts and stops the taskiq broker.

    Parameters
    ----------
    app : FastAPI
        The FastAPI application instance.
    """
    from sqlmodel import SQLModel

    from beanbay.database import engine
    from beanbay.seed import seed_brew_methods, seed_default_person, seed_stop_modes, seed_storage_types
    from beanbay.seed_optimization import seed_method_parameter_defaults

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        seed_brew_methods(session)
        seed_stop_modes(session)
        seed_storage_types(session)
        seed_default_person(session, settings.default_person_name)
        seed_method_parameter_defaults(session)
        session.commit()

    await broker.startup()
    yield
    await broker.shutdown()
```

- [ ] **Step 3: Move alembic from runtime to dev dependencies in pyproject.toml**

In `pyproject.toml`, remove `"alembic>=1.18.4",` from `[project] dependencies`.
Add it to `[dependency-groups] dev`:

```toml
[dependency-groups]
dev = [
    "alembic>=1.18.4",
    "pyright>=1.1.408",
]
```

- [ ] **Step 4: Run tests to verify nothing breaks**

```bash
uv sync
uv run pytest tests/ -v
```

Expected: all tests pass (tests use in-memory SQLite with `create_all`, not Alembic).

- [ ] **Step 5: Commit**

```bash
git add -u
git commit -m "refactor: replace alembic upgrade with create_all, clear migrations"
```

---

### Task 2: Add CLI Entrypoint

**Files:**
- Create: `src/beanbay/cli.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Create `src/beanbay/cli.py`**

```python
"""CLI entrypoint for BeanBay."""

import argparse


def main() -> None:
    """Start the BeanBay server."""
    import uvicorn

    parser = argparse.ArgumentParser(description="BeanBay")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    args = parser.parse_args()
    uvicorn.run("beanbay.main:app", host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Add scripts entry to pyproject.toml**

Add after the `[project.optional-dependencies]` section:

```toml
[project.scripts]
beanbay = "beanbay.cli:main"
```

- [ ] **Step 3: Reinstall and test the CLI**

```bash
uv sync
uv run beanbay --help
```

Expected: prints argparse help with `--port` flag.

- [ ] **Step 4: Commit**

```bash
git add src/beanbay/cli.py pyproject.toml
git commit -m "feat: add beanbay CLI entrypoint"
```

---

### Task 3: Add Static File Serving to FastAPI

**Files:**
- Modify: `src/beanbay/main.py:65-83`

- [ ] **Step 1: Add static file serving after the health endpoint**

First, add these imports at the top of `src/beanbay/main.py` (with the other
imports):

```python
from pathlib import Path

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
```

Then, at the bottom of the file, after the `health()` function, add:

```python
# --- Static file serving (production builds) ---
_static_dir = Path(__file__).parent / "static"
if _static_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=_static_dir / "assets"))

    @app.get("/{path:path}", include_in_schema=False)
    async def _spa_catch_all(path: str) -> FileResponse:
        """Serve index.html for all non-API routes (SPA client-side routing)."""
        return FileResponse(_static_dir / "index.html")
```

- [ ] **Step 2: Run tests to verify API routes still work**

```bash
uv run pytest tests/ -v
```

Expected: all pass. The `_static_dir.is_dir()` guard means the mount is skipped
when no build exists (dev mode and tests).

- [ ] **Step 3: Commit**

```bash
git add src/beanbay/main.py
git commit -m "feat: serve frontend static files from FastAPI"
```

---

### Task 4: Add Hatch Custom Build Hook

**Files:**
- Create: `hatch_build.py`
- Modify: `pyproject.toml`
- Modify: `.gitignore`

- [ ] **Step 1: Create `hatch_build.py` at repo root**

```python
"""Hatch custom build hook — builds the React frontend into the Python package."""

import os
import subprocess
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Build the frontend with bun and place output in src/beanbay/static/."""

    def initialize(self, version: str, build_data: dict) -> None:
        """Run the frontend build if static assets are not already present.

        Parameters
        ----------
        version : str
            The resolved package version string.
        build_data : dict
            Mutable mapping of build metadata.
        """
        root = Path(self.root)
        static_dir = root / "src" / "beanbay" / "static"
        manifest = static_dir / ".vite" / "manifest.json"

        if manifest.is_file():
            return

        frontend_dir = root / "frontend"
        if not frontend_dir.is_dir():
            return

        env = {**os.environ, "VITE_APP_VERSION": version}
        subprocess.run(["bun", "install"], cwd=frontend_dir, check=True, env=env)
        subprocess.run(
            ["bun", "run", "build:package"],
            cwd=frontend_dir,
            check=True,
            env=env,
        )
```

- [ ] **Step 2: Add hatch build config to pyproject.toml**

Add these sections to `pyproject.toml`:

```toml
[tool.hatch.build.hooks.custom]

[tool.hatch.build.targets.wheel]
packages = ["src/beanbay"]
artifacts = ["src/beanbay/static/"]
```

- [ ] **Step 3: Add `build:package` script to `frontend/package.json`**

Add to the `"scripts"` section:

```json
"build:package": "tsc -b && vite build --outDir ../../src/beanbay/static --emptyOutDir"
```

This is the script the hatch hook calls. It must exist before testing the build.

- [ ] **Step 4: Add static dir to .gitignore**

Append to `.gitignore`:

```
# Frontend build output (generated by hatch_build.py, included in wheels only)
src/beanbay/static/
```

- [ ] **Step 5: Test the build hook**

```bash
rm -rf src/beanbay/static
uv build --wheel
ls src/beanbay/static/index.html
```

Expected: the wheel build triggers `bun install && bun run build:package`, and
`src/beanbay/static/` contains `index.html` and `assets/`.

- [ ] **Step 6: Commit**

```bash
git add hatch_build.py pyproject.toml .gitignore frontend/package.json
git commit -m "feat: add hatch build hook to bundle frontend in wheel"
```

---

### Task 5: Add Dockerfile

**Files:**
- Create: `Dockerfile`
- Modify: `docker-compose.yml`
- Modify: `.dockerignore`

- [ ] **Step 1: Create the Dockerfile**

```dockerfile
# Stage 1: Build frontend with bun
FROM oven/bun:latest AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json frontend/bun.lock* ./
RUN bun install --frozen-lockfile

COPY frontend/ ./
RUN bun run build

# Stage 2: Build Python package
FROM python:3.11-slim AS python-builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY . .
COPY --from=frontend-builder /app/frontend/dist/ ./src/beanbay/static/

RUN uv pip install --system torch --index-url https://download.pytorch.org/whl/cpu \
    && uv pip install --system .

# Stage 3: Runtime
FROM python:3.11-slim

COPY --from=python-builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=python-builder /usr/local/bin/beanbay /usr/local/bin/beanbay

ENV BEANBAY_DATABASE_URL=sqlite:////data/beanbay.db
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /data

EXPOSE 8000
CMD ["beanbay"]
```

- [ ] **Step 2: Update docker-compose.yml**

Replace the environment variable in `docker-compose.yml`:

```yaml
services:
  beanbay:
    image: ghcr.io/grzonka/beanbay:latest
    container_name: beanbay
    ports:
      - "8000:8000"
    volumes:
      - beanbay-data:/data
    environment:
      - BEANBAY_DATABASE_URL=sqlite:////data/beanbay.db
    restart: unless-stopped

volumes:
  beanbay-data:
```

- [ ] **Step 3: Update .dockerignore**

Add `frontend/node_modules/` to `.dockerignore`:

```
frontend/node_modules/
```

- [ ] **Step 4: Commit**

```bash
git add Dockerfile docker-compose.yml .dockerignore
git commit -m "feat: add multi-stage Dockerfile, update compose"
```

---

### Task 6: Replace ESLint+Prettier with Biome

**Files:**
- Create: `frontend/biome.json`
- Modify: `frontend/package.json`
- Delete: `frontend/.eslintrc.cjs`
- Delete: `frontend/eslint.config.js`

- [ ] **Step 1: Create `frontend/biome.json`**

```json
{
  "$schema": "https://biomejs.dev/schemas/1.9.4/schema.json",
  "organizeImports": {
    "enabled": true
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true
    }
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "single"
    }
  }
}
```

- [ ] **Step 2: Update `frontend/package.json`**

Remove from `devDependencies`:
- `@eslint/js`
- `eslint`
- `eslint-plugin-react-hooks`
- `eslint-plugin-react-refresh`
- `globals`
- `prettier`
- `typescript-eslint`

Add to `devDependencies`:
- `@biomejs/biome`: `^1.9.4`

Change the `"lint"` script from `"eslint ."` to `"biome check ."`.

Add a `"build:package"` script for the hatch build hook:
```json
"build:package": "tsc -b && vite build --outDir ../../src/beanbay/static --emptyOutDir"
```

The resulting `devDependencies` should be:

```json
{
  "devDependencies": {
    "@biomejs/biome": "^1.9.4",
    "@types/lodash-es": "^4.17.12",
    "@types/node": "^24.12.0",
    "@types/react": "^19.2.14",
    "@types/react-dom": "^19.2.3",
    "@vitejs/plugin-react": "^6.0.1",
    "openapi-typescript": "^7.13.0",
    "typescript": "~5.9.3",
    "vite": "^8.0.1"
  }
}
```

- [ ] **Step 3: Delete old ESLint configs**

```bash
rm frontend/.eslintrc.cjs frontend/eslint.config.js
```

- [ ] **Step 4: Install and run biome to verify**

```bash
cd frontend && bun install && bun run lint
```

Expected: biome runs and reports any issues. Fix any auto-fixable issues with:

```bash
bunx @biomejs/biome check --write .
```

- [ ] **Step 5: Commit**

```bash
git add -u
git add frontend/biome.json
git commit -m "refactor: replace eslint+prettier with biome"
```

---

### Task 7: Add Pre-commit Configuration

**Files:**
- Create: `.pre-commit-config.yaml`

- [ ] **Step 1: Create `.pre-commit-config.yaml`**

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.13
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/biomejs/pre-commit
    rev: v2.0.0
    hooks:
      - id: biome-check
        additional_dependencies: ["@biomejs/biome@1.9.4"]
        files: ^frontend/src/
```

- [ ] **Step 2: Run pre-commit on all files**

```bash
uvx prek --all-files
```

Expected: all hooks pass (may auto-fix trailing whitespace or EOF issues on first run).

- [ ] **Step 3: Commit any auto-fixes and the config**

```bash
git add .pre-commit-config.yaml
git add -u
git commit -m "chore: add pre-commit with ruff and biome hooks"
```

---

### Task 8: CI Cleanup

**Files:**
- Modify: `.github/workflows/test.yml:29-30`

- [ ] **Step 1: Remove the ruff lint step from test.yml**

In `.github/workflows/test.yml`, delete lines 29-30:

```yaml
      - name: Lint
        run: ruff check app/ tests/
```

The file should end after the `Run tests` step.

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/test.yml
git commit -m "chore: remove stale ruff lint step from CI (handled by pre-commit)"
```

---

### Task 9: Final Verification

- [ ] **Step 1: Run the full test suite**

```bash
uv sync
uv run pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 2: Test the CLI**

```bash
uv run beanbay --port 9000 &
sleep 2
curl -s http://localhost:9000/health
kill %1
```

Expected: `{"status":"ok"}`

- [ ] **Step 3: Test wheel build includes static files**

```bash
rm -rf src/beanbay/static dist/
uv build --wheel
unzip -l dist/*.whl | grep static
```

Expected: wheel contains `beanbay/static/index.html` and `beanbay/static/assets/` files.

- [ ] **Step 4: Run pre-commit on all files**

```bash
uvx prek --all-files
```

Expected: all hooks pass.
