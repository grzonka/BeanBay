import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def uuid4_default() -> uuid.UUID:
    """Generate a new UUID4.

    Returns
    -------
    uuid.UUID
        A randomly generated UUID4.
    """
    return uuid.uuid4()


def now_utc() -> datetime:
    """Return the current UTC datetime.

    Returns
    -------
    datetime
        The current time in UTC.
    """
    return datetime.now(timezone.utc)
