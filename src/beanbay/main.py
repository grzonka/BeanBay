from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from beanbay.config import settings
from beanbay.routers.lookup import (
    bean_variety_router,
    brew_method_router,
    flavor_tag_router,
    origin_router,
    process_method_router,
    roaster_router,
    stop_mode_router,
    storage_type_router,
    vendor_router,
)
from beanbay.routers.beans import router as beans_router
from beanbay.routers.brew_setups import router as brew_setups_router
from beanbay.routers.brews import router as brews_router
from beanbay.routers.equipment import router as equipment_router
from beanbay.routers.people import router as people_router
from beanbay.routers.cuppings import router as cuppings_router
from beanbay.routers.ratings import router as ratings_router
from beanbay.routers.optimize import router as optimize_router
from beanbay.routers.stats import router as stats_router
from beanbay.services.taskiq_broker import broker


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan handler.

    Creates database tables, seeds default lookup data and the default
    person record.  Starts and stops the taskiq broker.

    Parameters
    ----------
    _app : FastAPI
        The FastAPI application instance.
    """
    from sqlmodel import SQLModel

    from beanbay.database import engine
    from beanbay.seed import (
        seed_brew_methods,
        seed_default_person,
        seed_stop_modes,
        seed_storage_types,
    )
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


app = FastAPI(title="BeanBay", lifespan=lifespan)

_routers = [
    flavor_tag_router,
    origin_router,
    roaster_router,
    process_method_router,
    bean_variety_router,
    brew_method_router,
    stop_mode_router,
    vendor_router,
    storage_type_router,
    people_router,
    equipment_router,
    beans_router,
    brew_setups_router,
    brews_router,
    cuppings_router,
    ratings_router,
    stats_router,
    optimize_router,
]
for _router in _routers:
    app.include_router(_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    """Return a simple health check response."""
    return {"status": "ok"}


# --- Static file serving (production builds) ---
_static_dir = Path(__file__).parent / "static"
if _static_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=_static_dir / "assets"))

    @app.get("/{path:path}", include_in_schema=False)
    async def _spa_catch_all(path: str) -> FileResponse:
        """Serve index.html for all non-API routes (SPA client-side routing)."""
        return FileResponse(_static_dir / "index.html")
