"""Shared FastAPI dependency types and helpers for BeanBay."""

from typing import Annotated

from fastapi import Depends, HTTPException
from sqlmodel import Session

from beanbay.database import get_session

SessionDep = Annotated[Session, Depends(get_session)]


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
