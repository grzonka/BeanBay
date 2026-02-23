import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String, Table, func
from sqlalchemy.orm import relationship

from app.database import Base


# Association table for Brewer <-> BrewMethod many-to-many relationship
brewer_methods = Table(
    "brewer_methods",
    Base.metadata,
    Column("brewer_id", String, ForeignKey("brewers.id"), primary_key=True),
    Column("method_id", String, ForeignKey("brew_methods.id"), primary_key=True),
)


class Grinder(Base):
    __tablename__ = "grinders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    dial_type = Column(String, nullable=False, default="stepless")  # "stepped" or "stepless"
    step_size = Column(Float, nullable=True)  # only meaningful when dial_type="stepped"
    min_value = Column(Float, nullable=True)  # minimum grind setting
    max_value = Column(Float, nullable=True)  # maximum grind setting
    is_retired = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())


class Brewer(Base):
    __tablename__ = "brewers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    is_retired = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())

    methods = relationship("BrewMethod", secondary="brewer_methods", backref="brewers")


class Paper(Base):
    __tablename__ = "papers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_retired = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())


class WaterRecipe(Base):
    __tablename__ = "water_recipes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    recipe_details = Column(String, nullable=True)
    notes = Column(String, nullable=True)  # how it was made
    gh = Column(Float, nullable=True)  # General Hardness
    kh = Column(Float, nullable=True)  # Carbonate Hardness
    ca = Column(Float, nullable=True)  # Calcium
    mg = Column(Float, nullable=True)  # Magnesium
    na = Column(Float, nullable=True)  # Sodium
    cl = Column(Float, nullable=True)  # Chloride
    so4 = Column(Float, nullable=True)  # Sulfate
    is_retired = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())
