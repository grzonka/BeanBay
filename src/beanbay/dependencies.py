"""Shared FastAPI dependency types and helpers for BeanBay."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Query
from sqlmodel import Session

from beanbay.database import get_session
from beanbay.models.person import Person

SessionDep = Annotated[Session, Depends(get_session)]


def _resolve_person_id(
    session: SessionDep,
    person_id: uuid.UUID | None = Query(default=None),
) -> uuid.UUID | None:
    """Resolve an optional person_id query parameter.

    Parameters
    ----------
    session : Session
        Database session.
    person_id : uuid.UUID | None
        Explicit person ID. If ``None``, returns ``None`` (no filter).

    Returns
    -------
    uuid.UUID | None
        The validated person ID, or ``None`` for unfiltered queries.

    Raises
    ------
    HTTPException
        404 if an explicit ``person_id`` is not found or is retired.
    """
    if person_id:
        person = session.get(Person, person_id)
        if not person or person.retired_at:
            raise HTTPException(status_code=404, detail="Person not found")
        return person_id
    return None


OptionalPersonIdDep = Annotated[uuid.UUID | None, Depends(_resolve_person_id)]


def validate_sort(sort_by: str, sort_dir: str, allowed: list[str]) -> None:
    """Raise 422 if sort parameters are invalid.

    Parameters
    ----------
    sort_by : str
        Field to sort by.
    sort_dir : str
        Sort direction: ``"asc"`` or ``"desc"``.
    allowed : list[str]
        Allowed sort fields.

    Raises
    ------
    HTTPException
        If ``sort_by`` is not in *allowed* or ``sort_dir`` is invalid.
    """
    if sort_by not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid sort_by field '{sort_by}'. Allowed: {allowed}",
        )
    if sort_dir not in ("asc", "desc"):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid sort_dir '{sort_dir}'. Must be 'asc' or 'desc'.",
        )
