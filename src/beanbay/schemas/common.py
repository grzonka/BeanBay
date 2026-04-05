"""Shared Pydantic schemas used across the BeanBay API."""

from collections.abc import Sequence
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """A paginated list response wrapper.

    Attributes
    ----------
    items : Sequence[T]
        The page of results.
    total : int
        Total number of matching records.
    limit : int
        Maximum items per page.
    offset : int
        Number of items skipped.
    """

    items: Sequence[T]
    total: int
    limit: int
    offset: int
