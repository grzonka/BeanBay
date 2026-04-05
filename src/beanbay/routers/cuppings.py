"""CRUD router for Cupping evaluations.

Endpoints for listing, creating, reading, updating, and retiring
SCAA-protocol cupping sessions with linked flavor tags.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func
from sqlmodel import select

from beanbay.dependencies import SessionDep, validate_sort
from beanbay.models.bean import Bag
from beanbay.models.cupping import Cupping, CuppingFlavorTagLink
from beanbay.models.person import Person
from beanbay.models.tag import FlavorTag
from beanbay.schemas.common import PaginatedResponse
from beanbay.schemas.cupping import CuppingCreate, CuppingRead, CuppingUpdate

router = APIRouter(tags=["Cuppings"])

CUPPING_SORT_FIELDS = ["cupped_at", "created_at", "total_score"]


def _set_flavor_tags(
    session: SessionDep,
    cupping: Cupping,
    flavor_tag_ids: list[uuid.UUID],
) -> None:
    """Replace M2M flavor tags on a cupping.

    Parameters
    ----------
    session : SessionDep
        Database session.
    cupping : Cupping
        The cupping to update.
    flavor_tag_ids : list[uuid.UUID]
        Flavor tag IDs to link.

    Raises
    ------
    HTTPException
        If a flavor tag is not found.
    """
    # Delete existing links
    existing_links = session.exec(
        select(CuppingFlavorTagLink).where(CuppingFlavorTagLink.cupping_id == cupping.id)
    ).all()
    for link in existing_links:
        session.delete(link)
    session.flush()

    # Add new links
    for tag_id in flavor_tag_ids:
        tag = session.get(FlavorTag, tag_id)
        if tag is None:
            raise HTTPException(
                status_code=404,
                detail=f"FlavorTag with id '{tag_id}' not found.",
            )
        session.add(CuppingFlavorTagLink(cupping_id=cupping.id, flavor_tag_id=tag_id))


# ======================================================================
# Cupping CRUD
# ======================================================================


@router.post("/cuppings", response_model=CuppingRead, status_code=201)
def create_cupping(
    payload: CuppingCreate,
    session: SessionDep,
) -> CuppingRead:
    """Create a new cupping evaluation.

    Parameters
    ----------
    payload : CuppingCreate
        Cupping creation data.
    session : SessionDep
        Database session (injected).

    Returns
    -------
    CuppingRead
        The created cupping.
    """
    # Validate bag exists and is not retired
    bag = session.get(Bag, payload.bag_id)
    if bag is None:
        raise HTTPException(status_code=404, detail="Bag not found.")
    if bag.retired_at is not None:
        raise HTTPException(status_code=409, detail="Bag is retired.")

    # Validate person exists
    person = session.get(Person, payload.person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found.")

    db_cupping = Cupping(
        bag_id=payload.bag_id,
        person_id=payload.person_id,
        cupped_at=payload.cupped_at,
        dry_fragrance=payload.dry_fragrance,
        wet_aroma=payload.wet_aroma,
        brightness=payload.brightness,
        flavor=payload.flavor,
        body=payload.body,
        finish=payload.finish,
        sweetness=payload.sweetness,
        clean_cup=payload.clean_cup,
        complexity=payload.complexity,
        uniformity=payload.uniformity,
        cuppers_correction=payload.cuppers_correction,
        total_score=payload.total_score,
        notes=payload.notes,
    )
    session.add(db_cupping)
    session.flush()

    # Handle flavor tag links
    if payload.flavor_tag_ids:
        _set_flavor_tags(session, db_cupping, payload.flavor_tag_ids)

    session.commit()
    session.refresh(db_cupping)
    return db_cupping  # type: ignore[return-value]


@router.get("/cuppings", response_model=PaginatedResponse[CuppingRead])
def list_cuppings(
    *,
    bag_id: uuid.UUID | None = Query(None, description="Filter by bag"),
    person_id: uuid.UUID | None = Query(None, description="Filter by person"),
    include_retired: bool = Query(False, description="Include soft-deleted items"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("cupped_at", description="Field to sort by"),
    sort_dir: str = Query("desc", description="Sort direction: asc or desc"),
    session: SessionDep,
) -> PaginatedResponse[CuppingRead]:
    """List cuppings with filtering, pagination, and sorting.

    Parameters
    ----------
    bag_id : uuid.UUID | None
        Optional filter by bag.
    person_id : uuid.UUID | None
        Optional filter by person.
    include_retired : bool
        When ``True``, include soft-deleted cuppings.
    limit : int
        Maximum items per page (1--200).
    offset : int
        Number of items to skip.
    sort_by : str
        Field to sort by.
    sort_dir : str
        Sort direction: ``"asc"`` or ``"desc"``.
    session : SessionDep
        Database session (injected).

    Returns
    -------
    PaginatedResponse[CuppingRead]
        Paginated response with ``items``, ``total``, ``limit``, ``offset``.
    """
    validate_sort(sort_by, sort_dir, CUPPING_SORT_FIELDS)

    stmt = select(Cupping)
    count_stmt = select(func.count()).select_from(Cupping)

    if not include_retired:
        stmt = stmt.where(Cupping.retired_at.is_(None))  # type: ignore[union-attr]
        count_stmt = count_stmt.where(Cupping.retired_at.is_(None))  # type: ignore[union-attr]

    if bag_id is not None:
        stmt = stmt.where(Cupping.bag_id == bag_id)
        count_stmt = count_stmt.where(Cupping.bag_id == bag_id)

    if person_id is not None:
        stmt = stmt.where(Cupping.person_id == person_id)
        count_stmt = count_stmt.where(Cupping.person_id == person_id)

    total: int = session.exec(count_stmt).one()  # type: ignore[arg-type]

    sort_column = getattr(Cupping, sort_by)
    if sort_dir == "desc":
        sort_column = sort_column.desc()
    stmt = stmt.order_by(sort_column)
    stmt = stmt.offset(offset).limit(limit)

    cuppings = session.exec(stmt).all()

    return PaginatedResponse(  # type: ignore[return-value]
        items=cuppings,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/cuppings/{cupping_id}", response_model=CuppingRead)
def get_cupping(
    cupping_id: uuid.UUID,
    session: SessionDep,
) -> CuppingRead:
    """Get a single cupping by ID.

    Parameters
    ----------
    cupping_id : uuid.UUID
        The cupping's primary key.
    session : SessionDep
        Database session (injected).

    Returns
    -------
    CuppingRead
        The cupping with nested flavor tags.
    """
    db_cupping = session.get(Cupping, cupping_id)
    if db_cupping is None:
        raise HTTPException(status_code=404, detail="Cupping not found.")
    return db_cupping  # type: ignore[return-value]


@router.patch("/cuppings/{cupping_id}", response_model=CuppingRead)
def update_cupping(
    cupping_id: uuid.UUID,
    payload: CuppingUpdate,
    session: SessionDep,
) -> CuppingRead:
    """Partially update a cupping.

    Parameters
    ----------
    cupping_id : uuid.UUID
        The cupping's primary key.
    payload : CuppingUpdate
        Fields to update.
    session : SessionDep
        Database session (injected).

    Returns
    -------
    CuppingRead
        The updated cupping.
    """
    db_cupping = session.get(Cupping, cupping_id)
    if db_cupping is None:
        raise HTTPException(status_code=404, detail="Cupping not found.")

    update_data = payload.model_dump(exclude_unset=True)

    # Handle flavor_tag_ids separately
    flavor_tag_ids = update_data.pop("flavor_tag_ids", None)

    db_cupping.sqlmodel_update(update_data)
    session.add(db_cupping)
    session.flush()

    if flavor_tag_ids is not None:
        _set_flavor_tags(session, db_cupping, flavor_tag_ids)

    session.commit()
    session.refresh(db_cupping)
    return db_cupping  # type: ignore[return-value]


@router.delete("/cuppings/{cupping_id}", response_model=CuppingRead)
def delete_cupping(
    cupping_id: uuid.UUID,
    session: SessionDep,
) -> CuppingRead:
    """Soft-delete a cupping.

    Parameters
    ----------
    cupping_id : uuid.UUID
        The cupping's primary key.
    session : SessionDep
        Database session (injected).

    Returns
    -------
    CuppingRead
        The soft-deleted cupping.
    """
    db_cupping = session.get(Cupping, cupping_id)
    if db_cupping is None:
        raise HTTPException(status_code=404, detail="Cupping not found.")

    db_cupping.retired_at = datetime.now(timezone.utc)
    session.add(db_cupping)
    session.commit()
    session.refresh(db_cupping)
    return db_cupping  # type: ignore[return-value]
