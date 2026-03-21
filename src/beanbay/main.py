from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Parameters
    ----------
    app : FastAPI
        The FastAPI application instance.
    """
    # TODO: Alembic migrations, seeding
    yield


app = FastAPI(title="BeanBay", lifespan=lifespan)


@app.get("/health")
def health():
    """Return a simple health check response."""
    return {"status": "ok"}
