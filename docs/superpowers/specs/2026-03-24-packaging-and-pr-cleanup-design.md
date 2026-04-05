# BeanBay Packaging, CLI & PR Cleanup Design

**Date:** 2026-03-24
**Status:** Draft
**Branch:** feat/refactor

## Goal

Package BeanBay as a single installable Python package that includes the React
frontend, provides a `beanbay` CLI entrypoint, and ships with a production
Dockerfile. Clean up stale Alembic migrations, CI lint config, and swap
ESLint+Prettier for Biome. Prepare the branch for a PR into main.

## 1. Hatch Custom Build Hook

A `hatch_build.py` at the repo root builds the frontend during
`pip install` / `uv sync` / wheel creation.

**Behavior:**
- Runs `bun install` then `bun run build --outDir ../../src/beanbay/static`
  inside `frontend/`. The `outDir` is passed as a CLI argument so
  `vite.config.ts` retains its default `dist/` output for standalone dev builds.
- Sets `VITE_APP_VERSION` env var from the Python package version.
- Skips the build if `src/beanbay/static/.vite/manifest.json` already exists
  (for Docker where assets are pre-copied). Checking the manifest is more
  robust than checking `index.html` alone.
- Requires `bun` on `PATH`. This is a dev/build prerequisite (documented in
  README).

**pyproject.toml additions:**
```toml
[tool.hatch.build.hooks.custom]

[tool.hatch.build.targets.wheel]
packages = ["src/beanbay"]
artifacts = ["src/beanbay/static/"]
```

**`.gitignore` addition:**
```
src/beanbay/static/
```

## 2. CLI Entrypoint

New file `src/beanbay/cli.py`:
- Uses `argparse` with a single `--port` flag (default `8000`).
- Hardcodes `host="0.0.0.0"`.
- Calls `uvicorn.run("beanbay.main:app", ...)`.

**pyproject.toml:**
```toml
[project.scripts]
beanbay = "beanbay.cli:main"
```

Usage: `beanbay` or `beanbay --port 3000`.
Power users run `uvicorn beanbay.main:app` directly.

## 3. FastAPI Static File Serving

Added at the bottom of `src/beanbay/main.py`, after all API routers:

```python
_static_dir = Path(__file__).parent / "static"
if _static_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=_static_dir / "assets"))

    @app.get("/{path:path}", include_in_schema=False)
    async def _spa_catch_all(path: str) -> FileResponse:
        return FileResponse(_static_dir / "index.html")
```

- `/assets` serves hashed JS/CSS bundles.
- `/{path:path}` catch-all serves `index.html` for client-side routing.
- Guard on `_static_dir.is_dir()` means dev mode (no build) still works;
  frontend runs via `bun run dev` with Vite proxy.
- Registered after API routers so `/api/v1/*` and `/health` always take
  priority.

## 4. Dockerfile

Three-stage build. No bun/node in the final image.

**Stage 1 (frontend-builder):**
- Base: `oven/bun:latest`
- Copies `frontend/`, runs `bun install && bun run build`.
- Output: built assets in `frontend/dist/`.

**Stage 2 (python-builder):**
- Base: `python:3.11-slim`
- Installs `uv`.
- Copies source tree + pre-built static from Stage 1 into
  `src/beanbay/static/`.
- Runs `uv pip install .` (hatch hook skips because static already present).
- CPU-only PyTorch via `--extra-index-url` (carried over from main branch
  pattern).

**Stage 3 (runtime):**
- Base: `python:3.11-slim`
- Copies installed site-packages from Stage 2.
- `ENV BEANBAY_DATABASE_URL=sqlite:////data/beanbay.db`, `PYTHONUNBUFFERED=1`.
- Creates `/data` directory.
- `EXPOSE 8000`.
- `CMD ["beanbay"]` (uses CLI entrypoint).

Note: `BEANBAY_DATA_DIR` is replaced by the concrete `BEANBAY_DATABASE_URL`
so the database is written to the mounted volume, not the container CWD.

## 5. Alembic Migration Reset

- Delete all files in `migrations/versions/`.
- Keep `migrations/env.py`, `migrations/script.py.mako`, `alembic.ini`.
- Replace `alembic.command.upgrade(cfg, "head")` in the lifespan handler with
  `SQLModel.metadata.create_all(engine)`. Remove Alembic imports from
  `main.py`.
- Move `alembic` from `[project.dependencies]` to
  `[dependency-groups] dev` since it is no longer needed at runtime (only for
  future CLI migration authoring).
- Alembic infrastructure remains for future schema evolution once the schema
  stabilizes.

## 6. Pre-commit & Linting

**New `.pre-commit-config.yaml`:**
- `pre-commit-hooks` (trailing whitespace, end-of-file fixer, YAML check).
- `ruff-pre-commit` (`ruff check --fix` + `ruff format`) for Python.
- `biome` for frontend TSX/TS/JS linting and formatting.

**Frontend tooling swap:**
- Add `@biomejs/biome` to `frontend/package.json` devDependencies.
- Add `frontend/biome.json` with recommended config.
- Remove ESLint dependencies (`eslint`, `@eslint/*`, `typescript-eslint`) and
  `prettier` from `package.json`.
- Update `"lint"` script in `package.json` from `"eslint ."` to
  `"biome check ."`.
- Delete `frontend/.eslintrc.cjs` and `frontend/eslint.config.js`.

**CI cleanup:**
- Remove the `ruff check app/ tests/` line from
  `.github/workflows/test.yml` (pre-commit handles linting).

## 7. Files Not Changed

These were reviewed and need no modifications:
- `docker-compose.yml` — already correct (pulls `ghcr.io/grzonka/beanbay:latest`,
  maps port 8000, data volume). Update `BEANBAY_DATA_DIR` env var to
  `BEANBAY_DATABASE_URL=sqlite:////data/beanbay.db` to match Dockerfile.
- `.github/workflows/docker-publish.yml` — already correct.
- `.dockerignore` — add `frontend/node_modules/` to reduce build context.

## 8. Complete Change Manifest

| Area | Action | File(s) |
|---|---|---|
| Build hook | Create | `hatch_build.py` |
| Build config | Modify | `pyproject.toml` |
| Docker compose | Modify | `docker-compose.yml` |
| Docker ignore | Modify | `.dockerignore` |
| CLI entrypoint | Create | `src/beanbay/cli.py` |
| Static serving | Modify | `src/beanbay/main.py` |
| Dockerfile | Create | `Dockerfile` |
| Migrations | Delete contents | `migrations/versions/*` |
| Lifespan handler | Modify | `src/beanbay/main.py` |
| Alembic dep | Move to dev | `pyproject.toml` |
| Pre-commit | Create | `.pre-commit-config.yaml` |
| Biome config | Create | `frontend/biome.json` |
| Frontend deps | Modify | `frontend/package.json` |
| ESLint configs | Delete | `frontend/.eslintrc.cjs`, `frontend/eslint.config.js` |
| CI lint | Modify | `.github/workflows/test.yml` |
| Gitignore | Modify | `.gitignore` |
