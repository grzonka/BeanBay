# BeanBay v0.1.0 Requirements — Release & Deploy

## Milestone Goal

Ship the existing v1 MVP as a properly branded, documented, and deployable product. Rebrand from BrewFlow to BeanBay, clean up tech debt, create a proper GitHub release, publish Docker image, and create Unraid Community Apps template.

## Requirements

### Branding & Identity

| ID | Requirement | Priority |
|----|-------------|----------|
| BRAND-01 | Rename project from BrewFlow to BeanBay across all code, config, templates, and metadata | Must |
| BRAND-02 | Update UI title, page headers, and meta tags to reflect BeanBay branding | Must |
| BRAND-03 | Create app icon/logo for Docker image, Unraid template, and GitHub repo | Should |

### Repository Cleanup

| ID | Requirement | Priority |
|----|-------------|----------|
| CLEAN-01 | Remove legacy files not part of BeanBay (my_espresso.py, __marimo__/, baybe-resources references) | Must |
| CLEAN-02 | Remove dead app/routes/ directory (actual routers live in app/routers/) | Must |
| CLEAN-03 | Create comprehensive README.md with project description, screenshots placeholder, setup instructions, Docker usage, and development guide | Must |
| CLEAN-04 | LICENSE file present (Apache 2.0, already added via GitHub) | Should |

### Tech Debt

| ID | Requirement | Priority |
|----|-------------|----------|
| DEBT-01 | Extract duplicated _get_active_bean helper from brew.py and insights.py into shared utility | Must |
| DEBT-02 | Persist pending_recommendations to database/file instead of in-memory dict (survives restart) | Must |
| DEBT-03 | Move startup ALTER TABLE migration into proper Alembic migration | Should |
| DEBT-04 | Surface error feedback on invalid parameter override parsing instead of silent ValueError | Should |

### Docker & Deployment

| ID | Requirement | Priority |
|----|-------------|----------|
| DEPLOY-01 | Update Dockerfile and docker-compose.yml with BeanBay naming (service name, volume, env vars) | Must |
| DEPLOY-02 | Publish Docker image to GitHub Container Registry (ghcr.io/grzonka/beanbay) | Must |
| DEPLOY-03 | Create GitHub Actions workflow for automated Docker image builds on release tags | Must |
| DEPLOY-04 | Create Unraid Community Apps XML template in repository | Must |

### Release

| ID | Requirement | Priority |
|----|-------------|----------|
| REL-01 | Create GitHub release v0.1.0 with changelog and release notes | Must |
| REL-02 | Ensure all 108+ existing tests pass after rebrand | Must |

---

**Total: 16 requirements (11 Must, 5 Should)**
**Milestone type: Release & Deploy (no new features)**

---

## Traceability

| ID | Requirement | Phase | Status |
|----|-------------|-------|--------|
| BRAND-01 | Rename BrewFlow to BeanBay in all code/config/templates | 7 | Complete |
| BRAND-02 | Update UI title, headers, meta tags | 7 | Complete |
| BRAND-03 | Create app icon/logo | 9 | Deferred |
| CLEAN-01 | Remove legacy files (my_espresso.py, __marimo__/) | 7 | Complete |
| CLEAN-02 | Remove dead app/routes/ directory | 7 | Complete |
| CLEAN-03 | Create comprehensive README.md | 8 | Complete |
| CLEAN-04 | LICENSE file present | 8 | Complete |
| DEBT-01 | Deduplicate _get_active_bean helper | 7 | Complete |
| DEBT-02 | Persist pending_recommendations | 7 | Complete |
| DEBT-03 | Move ALTER TABLE to Alembic migration | 7 | Complete |
| DEBT-04 | Surface error on invalid override parsing | 7 | Complete |
| DEPLOY-01 | Update Docker files with BeanBay naming | 9 | Complete |
| DEPLOY-02 | Publish Docker image to ghcr.io | 9 | Complete |
| DEPLOY-03 | GitHub Actions CI/CD workflow | 8 | Complete |
| DEPLOY-04 | Unraid Community Apps XML template | 9 | Complete |
| REL-01 | Create GitHub release v0.1.0 | 8 | Complete |
| REL-02 | All 108+ tests pass after rebrand | 7 | Complete |
