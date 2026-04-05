"""Bean and Bag models for BeanBay.

Bean represents a coffee bean with many-to-many relationships to Origin,
ProcessMethod, and BeanVariety, a foreign key to Roaster, and a
one-to-many relationship to Bag.

Bag represents a physical bag of a particular bean, tracking weight,
price, roast date, and whether it is pre-ground.
"""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Column, DateTime as SADateTime, func
from sqlmodel import Field, Relationship, SQLModel

from beanbay.models.base import uuid4_default
from beanbay.models.enums import BeanMixType, BeanUseType


# ---------------------------------------------------------------------------
# Junction / link models for Bean M2M
# ---------------------------------------------------------------------------


class BeanOriginLink(SQLModel, table=True):
    """Link table between Bean and Origin.

    Attributes
    ----------
    bean_id : uuid.UUID
        Foreign key to the bean.
    origin_id : uuid.UUID
        Foreign key to the origin.
    percentage : float | None
        Blend percentage for this origin (0--100). ``None`` if not specified.
    """

    __tablename__ = "bean_origins"  # type: ignore[assignment]

    bean_id: uuid.UUID = Field(foreign_key="beans.id", primary_key=True)
    origin_id: uuid.UUID = Field(foreign_key="origins.id", primary_key=True)
    percentage: float | None = None


class BeanProcessLink(SQLModel, table=True):
    """Link table between Bean and ProcessMethod.

    Attributes
    ----------
    bean_id : uuid.UUID
        Foreign key to the bean.
    process_id : uuid.UUID
        Foreign key to the process method.
    """

    __tablename__ = "bean_processes"  # type: ignore[assignment]

    bean_id: uuid.UUID = Field(foreign_key="beans.id", primary_key=True)
    process_id: uuid.UUID = Field(foreign_key="process_methods.id", primary_key=True)


class BeanVarietyLink(SQLModel, table=True):
    """Link table between Bean and BeanVariety.

    Attributes
    ----------
    bean_id : uuid.UUID
        Foreign key to the bean.
    variety_id : uuid.UUID
        Foreign key to the bean variety.
    """

    __tablename__ = "bean_variety_links"  # type: ignore[assignment]

    bean_id: uuid.UUID = Field(foreign_key="beans.id", primary_key=True)
    variety_id: uuid.UUID = Field(foreign_key="bean_varieties.id", primary_key=True)


class BeanFlavorTagLink(SQLModel, table=True):
    """Link table between Bean and FlavorTag (roaster's claimed flavors).

    Attributes
    ----------
    bean_id : uuid.UUID
        Foreign key to the bean.
    flavor_tag_id : uuid.UUID
        Foreign key to the flavor tag.
    """

    __tablename__ = "bean_flavor_tags"  # type: ignore[assignment]

    bean_id: uuid.UUID = Field(foreign_key="beans.id", primary_key=True)
    flavor_tag_id: uuid.UUID = Field(foreign_key="flavor_tags.id", primary_key=True)


# ---------------------------------------------------------------------------
# Bean model
# ---------------------------------------------------------------------------


class Bean(SQLModel, table=True):
    """A coffee bean entry.

    Attributes
    ----------
    id : uuid.UUID
        Primary key.
    name : str
        Name of the bean / blend.
    roaster_id : uuid.UUID | None
        Foreign key to the roaster.
    notes : str | None
        Free-text notes.
    roast_degree : float | None
        Roast degree on a 0--10 scale.
    bean_mix_type : BeanMixType
        Whether the bean is single origin, blend, or unknown.
    bean_use_type : BeanUseType | None
        Roaster's intended use (filter, espresso, omni).
    decaf : bool
        Whether the bean is decaffeinated.
    url : str | None
        URL to the roaster's product page.
    ean : str | None
        EAN / barcode for the bean.
    created_at : datetime
        Row creation timestamp (server default).
    updated_at : datetime
        Last-modified timestamp (server default, auto-updated).
    retired_at : datetime | None
        Soft-delete timestamp; ``None`` while active.
    """

    __tablename__ = "beans"  # type: ignore[assignment]

    id: uuid.UUID = Field(default_factory=uuid4_default, primary_key=True)
    name: str = Field(index=True)
    roaster_id: uuid.UUID | None = Field(default=None, foreign_key="roasters.id")
    notes: str | None = None
    roast_degree: float | None = None
    bean_mix_type: BeanMixType = Field(default=BeanMixType.UNKNOWN)
    bean_use_type: BeanUseType | None = None
    decaf: bool = Field(default=False)
    url: str | None = None
    ean: str | None = None
    created_at: datetime = Field(
        default=None,
        sa_column=Column(SADateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime = Field(
        default=None,
        sa_column=Column(SADateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )
    retired_at: datetime | None = None

    # Relationships
    roaster: Optional["Roaster"] = Relationship(  # type: ignore[name-defined]  # noqa: F821
    )
    bags: list["Bag"] = Relationship(back_populates="bean")
    origins: list["Origin"] = Relationship(  # type: ignore[name-defined]  # noqa: F821
        link_model=BeanOriginLink,
    )
    processes: list["ProcessMethod"] = Relationship(  # type: ignore[name-defined]  # noqa: F821
        link_model=BeanProcessLink,
    )
    varieties: list["BeanVariety"] = Relationship(  # type: ignore[name-defined]  # noqa: F821
        link_model=BeanVarietyLink,
    )
    flavor_tags: list["FlavorTag"] = Relationship(  # type: ignore[name-defined]  # noqa: F821
        link_model=BeanFlavorTagLink,
    )


# ---------------------------------------------------------------------------
# Bag model
# ---------------------------------------------------------------------------


class Bag(SQLModel, table=True):
    """A physical bag of coffee beans.

    Attributes
    ----------
    id : uuid.UUID
        Primary key.
    bean_id : uuid.UUID
        Foreign key to the parent bean.
    roast_date : date | None
        Date the coffee was roasted.
    opened_at : date | None
        Date the bag was opened.
    weight : float
        Weight in grams (canonical unit).
    price : float | None
        Price paid for the bag.
    is_preground : bool
        Whether the coffee is pre-ground.
    notes : str | None
        Free-text notes.
    bought_at : date | None
        Date the bag was purchased.
    vendor_id : uuid.UUID | None
        Foreign key to the vendor / shop.
    frozen_at : datetime | None
        Timestamp when the bag was frozen.
    thawed_at : datetime | None
        Timestamp when the bag was thawed.
    storage_type_id : uuid.UUID | None
        Foreign key to the frozen-storage type.
    best_date : date | None
        Best-before date.
    created_at : datetime
        Row creation timestamp (server default).
    updated_at : datetime
        Last-modified timestamp (server default, auto-updated).
    retired_at : datetime | None
        Soft-delete timestamp; ``None`` while active.
    """

    __tablename__ = "bags"  # type: ignore[assignment]

    id: uuid.UUID = Field(default_factory=uuid4_default, primary_key=True)
    bean_id: uuid.UUID = Field(foreign_key="beans.id")
    roast_date: date | None = None
    opened_at: date | None = None
    weight: float
    price: float | None = None
    is_preground: bool = Field(default=False)
    notes: str | None = None
    bought_at: date | None = None
    vendor_id: uuid.UUID | None = Field(default=None, foreign_key="vendors.id")
    frozen_at: datetime | None = None
    thawed_at: datetime | None = None
    storage_type_id: uuid.UUID | None = Field(default=None, foreign_key="storage_types.id")
    best_date: date | None = None
    created_at: datetime = Field(
        default=None,
        sa_column=Column(SADateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime = Field(
        default=None,
        sa_column=Column(SADateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )
    retired_at: datetime | None = None

    # Relationships
    bean: Bean = Relationship(back_populates="bags")
    vendor: Optional["Vendor"] = Relationship()  # type: ignore[name-defined]  # noqa: F821
    storage_type: Optional["StorageType"] = Relationship()  # type: ignore[name-defined]  # noqa: F821
