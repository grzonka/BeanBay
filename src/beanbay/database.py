from collections.abc import Generator

from sqlalchemy import event
from sqlmodel import Session, create_engine

from beanbay.config import settings

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(settings.database_url, connect_args=connect_args)

if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _set_sqlite_wal(dbapi_connection, connection_record):
        """Enable WAL journal mode for SQLite connections."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


def get_session() -> Generator[Session, None, None]:
    """Yield a SQLModel session for FastAPI dependency injection.

    Yields
    ------
    Session
        A SQLModel database session.
    """
    with Session(engine) as session:
        yield session
