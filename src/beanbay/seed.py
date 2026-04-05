"""Seed data for BeanBay startup.

Idempotent seed functions that populate default lookup values
and a default person record.
"""

from sqlmodel import Session, select

from beanbay.models.person import Person
from beanbay.models.tag import BrewMethod, StopMode, StorageType


def seed_brew_methods(session: Session) -> None:
    """Insert default brew methods if they do not already exist.

    Parameters
    ----------
    session : Session
        An active SQLModel session.
    """
    defaults = [
        "espresso",
        "pour-over",
        "french-press",
        "aeropress",
        "turkish",
        "moka-pot",
        "cold-brew",
    ]
    for name in defaults:
        existing = session.exec(select(BrewMethod).where(BrewMethod.name == name)).first()
        if not existing:
            session.add(BrewMethod(name=name))


def seed_stop_modes(session: Session) -> None:
    """Insert default stop modes if they do not already exist.

    Parameters
    ----------
    session : Session
        An active SQLModel session.
    """
    defaults = ["manual", "timed", "volumetric", "gravimetric"]
    for name in defaults:
        existing = session.exec(select(StopMode).where(StopMode.name == name)).first()
        if not existing:
            session.add(StopMode(name=name))


def seed_default_person(session: Session, name: str) -> None:
    """Insert a default person if one with the given name does not exist.

    Parameters
    ----------
    session : Session
        An active SQLModel session.
    name : str
        The name for the default person.
    """
    existing = session.exec(select(Person).where(Person.name == name)).first()
    if not existing:
        session.add(Person(name=name, is_default=True))


def seed_storage_types(session: Session) -> None:
    """Insert default storage types if they do not already exist.

    Parameters
    ----------
    session : Session
        An active SQLModel session.
    """
    defaults = ["Vacuum Sealed", "Zip Lock", "Coffee Bag", "Coffee Jar", "Tube"]
    for name in defaults:
        existing = session.exec(select(StorageType).where(StorageType.name == name)).first()
        if not existing:
            session.add(StorageType(name=name))
