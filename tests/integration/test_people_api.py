"""Integration tests for the Person CRUD endpoints.

Tests cover creation, listing, updating (including default-person swap),
soft-delete, duplicate-name handling, and the computed ``is_retired`` field.
"""

import uuid


BASE = "/api/v1/people"


class TestPersonCreate:
    """POST /api/v1/people"""

    def test_create_returns_201(self, client):
        """POST creates a person and returns 201 with all expected fields."""
        resp = client.post(BASE, json={"name": "Alice"})
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Alice"
        assert "id" in body
        assert "created_at" in body
        assert "updated_at" in body
        assert body["is_default"] is False
        assert body["is_retired"] is False
        assert body["retired_at"] is None

    def test_create_duplicate_name_returns_409(self, client):
        """POST with a duplicate name returns 409 Conflict."""
        client.post(BASE, json={"name": "DuplicatePerson"})
        resp = client.post(BASE, json={"name": "DuplicatePerson"})
        assert resp.status_code == 409


class TestPersonList:
    """GET /api/v1/people"""

    def test_list_returns_paginated(self, client):
        """GET / returns items, total, limit, offset."""
        client.post(BASE, json={"name": "Bob"})
        client.post(BASE, json={"name": "Carol"})
        resp = client.get(BASE)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "limit" in body
        assert "offset" in body
        assert body["total"] >= 2


class TestPersonGetById:
    """GET /api/v1/people/{id}"""

    def test_get_by_id(self, client):
        """GET /{id} returns the person."""
        r = client.post(BASE, json={"name": "Dave"})
        person_id = r.json()["id"]
        resp = client.get(f"{BASE}/{person_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Dave"

    def test_get_not_found(self, client):
        """GET /{id} with unknown id returns 404."""
        fake_id = str(uuid.uuid4())
        resp = client.get(f"{BASE}/{fake_id}")
        assert resp.status_code == 404


class TestPersonUpdate:
    """PATCH /api/v1/people/{id}"""

    def test_patch_updates_name(self, client):
        """PATCH /{id} updates the name."""
        r = client.post(BASE, json={"name": "OldPersonName"})
        person_id = r.json()["id"]
        resp = client.patch(f"{BASE}/{person_id}", json={"name": "NewPersonName"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "NewPersonName"

    def test_patch_set_default_unsets_previous(self, client):
        """PATCH /{id} with is_default=true unsets the previous default."""
        # Create two people
        r1 = client.post(BASE, json={"name": "PersonA"})
        r2 = client.post(BASE, json={"name": "PersonB"})
        id_a = r1.json()["id"]
        id_b = r2.json()["id"]

        # Set A as default
        resp_a = client.patch(f"{BASE}/{id_a}", json={"is_default": True})
        assert resp_a.status_code == 200
        assert resp_a.json()["is_default"] is True

        # Set B as default — A should be unset
        resp_b = client.patch(f"{BASE}/{id_b}", json={"is_default": True})
        assert resp_b.status_code == 200
        assert resp_b.json()["is_default"] is True

        # Verify A is no longer the default
        resp_check = client.get(f"{BASE}/{id_a}")
        assert resp_check.json()["is_default"] is False


class TestPersonDelete:
    """DELETE /api/v1/people/{id}"""

    def test_delete_soft_deletes(self, client):
        """DELETE /{id} sets retired_at and returns the person."""
        r = client.post(BASE, json={"name": "ToRetirePerson"})
        person_id = r.json()["id"]
        resp = client.delete(f"{BASE}/{person_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["retired_at"] is not None
        assert body["is_retired"] is True

    def test_delete_not_found(self, client):
        """DELETE /{id} with unknown id returns 404."""
        fake_id = str(uuid.uuid4())
        resp = client.delete(f"{BASE}/{fake_id}")
        assert resp.status_code == 404


class TestPersonReadSchema:
    """Verify the PersonRead schema includes computed fields."""

    def test_is_retired_computed_field(self, client):
        """PersonRead includes is_retired computed from retired_at."""
        r = client.post(BASE, json={"name": "ComputedFieldPerson"})
        body = r.json()

        # Active person: is_retired should be False
        assert body["is_retired"] is False
        assert body["retired_at"] is None

        # Soft-delete and check again
        person_id = body["id"]
        resp = client.delete(f"{BASE}/{person_id}")
        body = resp.json()
        assert body["is_retired"] is True
        assert body["retired_at"] is not None
