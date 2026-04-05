"""Tests for seed data idempotency."""

from sqlmodel import select

from beanbay.models.person import Person
from beanbay.models.tag import BrewMethod, StopMode
from beanbay.seed import seed_brew_methods, seed_default_person, seed_stop_modes


def test_seed_brew_methods_idempotent(session):
    """Calling seed_brew_methods twice produces exactly 7 methods."""
    seed_brew_methods(session)
    session.commit()
    seed_brew_methods(session)
    session.commit()

    methods = session.exec(select(BrewMethod)).all()
    assert len(methods) == 7
    names = {m.name for m in methods}
    assert names == {
        "espresso",
        "pour-over",
        "french-press",
        "aeropress",
        "turkish",
        "moka-pot",
        "cold-brew",
    }


def test_seed_stop_modes_idempotent(session):
    """Calling seed_stop_modes twice produces exactly 4 modes."""
    seed_stop_modes(session)
    session.commit()
    seed_stop_modes(session)
    session.commit()

    modes = session.exec(select(StopMode)).all()
    assert len(modes) == 4
    names = {m.name for m in modes}
    assert names == {"manual", "timed", "volumetric", "gravimetric"}


def test_seed_default_person_idempotent(session):
    """Calling seed_default_person twice produces exactly 1 person."""
    seed_default_person(session, "Default")
    session.commit()
    seed_default_person(session, "Default")
    session.commit()

    people = session.exec(select(Person).where(Person.name == "Default")).all()
    assert len(people) == 1
    assert people[0].is_default is True


def test_seed_storage_types(session):
    """Calling seed_storage_types inserts the expected default types."""
    from beanbay.models.tag import StorageType
    from beanbay.seed import seed_storage_types

    seed_storage_types(session)
    session.commit()

    types = session.exec(select(StorageType)).all()
    names = {t.name for t in types}
    assert {"Vacuum Sealed", "Zip Lock", "Coffee Bag", "Coffee Jar", "Tube"} <= names
