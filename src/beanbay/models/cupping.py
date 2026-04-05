"""Cupping model for SCAA-protocol coffee evaluations."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime as SADateTime, func
from sqlmodel import Field, Relationship, SQLModel

from beanbay.models.base import uuid4_default

if TYPE_CHECKING:
    from beanbay.models.bean import Bag
    from beanbay.models.person import Person
    from beanbay.models.tag import FlavorTag


class CuppingFlavorTagLink(SQLModel, table=True):
    """Link table between Cupping and FlavorTag.

    Attributes
    ----------
    cupping_id : uuid.UUID
        Foreign key to the cupping.
    flavor_tag_id : uuid.UUID
        Foreign key to the flavor tag.
    """

    __tablename__ = "cupping_flavor_tags"  # type: ignore[assignment]
    cupping_id: uuid.UUID = Field(foreign_key="cuppings.id", primary_key=True)
    flavor_tag_id: uuid.UUID = Field(foreign_key="flavor_tags.id", primary_key=True)


class Cupping(SQLModel, table=True):
    """An SCAA-protocol cupping evaluation of a bag of coffee.

    Attributes
    ----------
    id : uuid.UUID
        Primary key.
    bag_id : uuid.UUID
        Foreign key to the bag being cupped.
    person_id : uuid.UUID
        Foreign key to the person who cupped.
    cupped_at : datetime
        When the cupping session happened.
    dry_fragrance : float | None
        Ground coffee aroma (0-9 SCAA).
    wet_aroma : float | None
        Aroma after adding water (0-9).
    brightness : float | None
        Acidity / vibrancy (0-9).
    flavor : float | None
        Overall taste quality (0-9).
    body : float | None
        Weight / mouthfeel (0-9).
    finish : float | None
        Aftertaste length and quality (0-9).
    sweetness : float | None
        Sweetness (0-9).
    clean_cup : float | None
        Absence of defects (0-9).
    complexity : float | None
        Flavor layers / depth (0-9).
    uniformity : float | None
        Cup-to-cup consistency (0-9).
    cuppers_correction : float | None
        Personal adjustment (can be negative).
    total_score : float | None
        0-100 SCAA scale.
    notes : str | None
        Free-text notes.
    created_at : datetime
        Row creation timestamp.
    updated_at : datetime
        Last-modified timestamp.
    retired_at : datetime | None
        Soft-delete timestamp.
    """

    __tablename__ = "cuppings"  # type: ignore[assignment]

    id: uuid.UUID = Field(default_factory=uuid4_default, primary_key=True)
    bag_id: uuid.UUID = Field(foreign_key="bags.id")
    person_id: uuid.UUID = Field(foreign_key="people.id")
    cupped_at: datetime

    dry_fragrance: float | None = None
    wet_aroma: float | None = None
    brightness: float | None = None
    flavor: float | None = None
    body: float | None = None
    finish: float | None = None
    sweetness: float | None = None
    clean_cup: float | None = None
    complexity: float | None = None
    uniformity: float | None = None
    cuppers_correction: float | None = None
    total_score: float | None = None
    notes: str | None = None

    created_at: datetime = Field(
        default=None,
        sa_column=Column(SADateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime = Field(
        default=None,
        sa_column=Column(SADateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )
    retired_at: Optional[datetime] = None

    bag: "Bag" = Relationship()
    person: "Person" = Relationship()
    flavor_tags: list["FlavorTag"] = Relationship(link_model=CuppingFlavorTagLink)
