"""BeanBay — FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, SessionLocal, engine, get_db
from app.routers import analytics, beans, brew, equipment, history, insights
from app.services.migration import (
    migrate_campaigns_to_db,
    migrate_legacy_campaign_files,
    migrate_pending_to_db,
)
from app.services.optimizer import OptimizerService

# Import models so they're registered with Base
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    import logging as _logging

    _log = _logging.getLogger(__name__)

    # Startup: ensure data directory exists
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    # Create tables if they don't exist (no-op if Alembic already ran)
    Base.metadata.create_all(bind=engine)

    # Rename legacy campaign files (bare bean_id → new key format) before DB migration
    campaigns_dir = settings.data_dir / "campaigns"
    _migrated_files = migrate_legacy_campaign_files(campaigns_dir)
    if _migrated_files:
        _log.info("Renamed %d legacy campaign file(s) to new key format", _migrated_files)

    # Migrate campaign files from disk into DB (idempotent)
    _migrated_campaigns = migrate_campaigns_to_db(SessionLocal, campaigns_dir)
    if _migrated_campaigns:
        _log.info("Migrated %d campaign(s) from disk to DB", _migrated_campaigns)

    # Migrate pending recommendations from disk into DB (idempotent)
    _migrated_pending = migrate_pending_to_db(SessionLocal, settings.data_dir)
    if _migrated_pending:
        _log.info("Migrated %d pending recommendation(s) from disk to DB", _migrated_pending)

    # Initialize optimizer service with DB-backed session factory
    app.state.optimizer = OptimizerService(SessionLocal)

    yield
    # Shutdown: nothing to clean up


app = FastAPI(title="BeanBay", lifespan=lifespan)

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir, check_dir=False), name="static")

# Include routers
app.include_router(beans.router)
app.include_router(brew.router)
app.include_router(equipment.router)
app.include_router(history.router)
app.include_router(insights.router)
app.include_router(analytics.router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "beanbay"}


templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    """Show welcome page if no beans exist, otherwise redirect to beans."""
    from app.models.bean import Bean

    bean_count = db.query(Bean).count()
    if bean_count == 0:
        return templates.TemplateResponse(request, "welcome.html")
    return RedirectResponse(url="/beans", status_code=303)
