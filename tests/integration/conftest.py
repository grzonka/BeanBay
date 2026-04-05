"""Integration-test fixtures shared by all tests under tests/integration/.

Provides ``recommend_engine``, ``recommend_session`` and ``recommend_client``
fixtures that use ``StaticPool`` so the taskiq ``generate_recommendation``
task (which opens its own ``Session(engine)``) shares the same in-memory
SQLite connection as the test session.
"""

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import beanbay.database
import beanbay.services.taskiq_broker
from beanbay.database import get_session
from beanbay.main import app


@pytest.fixture()
def recommend_engine(monkeypatch):
    """Create a StaticPool engine and patch it into beanbay.database.

    This ensures the taskiq broker task and the test session share
    the same underlying SQLite connection so data is visible to both.
    """
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(eng)
    monkeypatch.setattr(beanbay.database, "engine", eng)
    monkeypatch.setattr(beanbay.services.taskiq_broker, "engine", eng)
    yield eng


@pytest.fixture()
def recommend_session(recommend_engine):
    """Provide a session bound to the shared StaticPool engine."""
    with Session(recommend_engine) as session:
        yield session


@pytest.fixture()
def recommend_client(recommend_session):
    """Provide a TestClient wired to the recommend_session."""
    from fastapi.testclient import TestClient

    def get_session_override():
        yield recommend_session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
