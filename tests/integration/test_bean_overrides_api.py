"""Integration tests for Bean Parameter Override endpoints.

Covers listing, creating, replacing, and clearing bean parameter overrides,
as well as 404 handling for missing beans.
"""

import uuid

BEANS = "/api/v1/beans"
OVERRIDES_URL = "/api/v1/optimize/beans/{bean_id}/overrides"


# ======================================================================
# Helpers
# ======================================================================


def _unique(prefix: str) -> str:
    """Return a unique name to avoid collisions across tests."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _create_bean(client, name: str | None = None) -> str:
    """Create a bean and return its id."""
    name = name or _unique("bean")
    resp = client.post(BEANS, json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


def _overrides_url(bean_id: str) -> str:
    """Build the overrides URL for a given bean_id."""
    return OVERRIDES_URL.format(bean_id=bean_id)


# ======================================================================
# Tests
# ======================================================================


def test_list_overrides_empty(client):
    """GET returns empty list for a bean with no overrides."""
    bean_id = _create_bean(client)
    resp = client.get(_overrides_url(bean_id))
    assert resp.status_code == 200
    assert resp.json() == []


def test_put_overrides_returns_created(client):
    """PUT with valid overrides returns 200 and the created overrides."""
    bean_id = _create_bean(client)
    payload = {
        "overrides": [
            {"parameter_name": "temperature", "min_value": 90.0, "max_value": 96.0},
            {"parameter_name": "dose", "min_value": 16.0, "max_value": 20.0},
        ]
    }
    resp = client.put(_overrides_url(bean_id), json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert len(data) == 2

    names = {item["parameter_name"] for item in data}
    assert names == {"temperature", "dose"}

    for item in data:
        assert "id" in item
        assert item["bean_id"] == bean_id
        assert "created_at" in item
        assert "updated_at" in item


def test_get_after_put_returns_overrides(client):
    """GET after PUT returns the same overrides that were set."""
    bean_id = _create_bean(client)
    payload = {
        "overrides": [
            {"parameter_name": "pressure", "min_value": 6.0, "max_value": 9.0},
        ]
    }
    client.put(_overrides_url(bean_id), json=payload)

    resp = client.get(_overrides_url(bean_id))
    assert resp.status_code == 200

    data = resp.json()
    assert len(data) == 1
    assert data[0]["parameter_name"] == "pressure"
    assert data[0]["min_value"] == 6.0
    assert data[0]["max_value"] == 9.0


def test_put_replaces_all_overrides(client):
    """A second PUT replaces all previous overrides."""
    bean_id = _create_bean(client)

    # First PUT
    payload1 = {
        "overrides": [
            {"parameter_name": "temperature", "min_value": 90.0, "max_value": 96.0},
            {"parameter_name": "dose", "min_value": 16.0, "max_value": 20.0},
        ]
    }
    client.put(_overrides_url(bean_id), json=payload1)

    # Second PUT with different overrides
    payload2 = {
        "overrides": [
            {"parameter_name": "yield_amount", "min_value": 30.0, "max_value": 45.0},
        ]
    }
    resp = client.put(_overrides_url(bean_id), json=payload2)
    assert resp.status_code == 200

    data = resp.json()
    assert len(data) == 1
    assert data[0]["parameter_name"] == "yield_amount"

    # Confirm via GET
    resp = client.get(_overrides_url(bean_id))
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["parameter_name"] == "yield_amount"


def test_put_empty_list_clears_overrides(client):
    """PUT with an empty overrides list removes all overrides."""
    bean_id = _create_bean(client)

    # Set some overrides first
    payload = {
        "overrides": [
            {"parameter_name": "temperature", "min_value": 90.0, "max_value": 96.0},
        ]
    }
    client.put(_overrides_url(bean_id), json=payload)

    # Clear with empty list
    resp = client.put(_overrides_url(bean_id), json={"overrides": []})
    assert resp.status_code == 200
    assert resp.json() == []

    # Confirm via GET
    resp = client.get(_overrides_url(bean_id))
    assert resp.status_code == 200
    assert resp.json() == []


def test_put_invalid_bean_id_returns_404(client):
    """PUT with a nonexistent bean_id returns 404."""
    fake_id = str(uuid.uuid4())
    payload = {
        "overrides": [
            {"parameter_name": "temperature", "min_value": 90.0, "max_value": 96.0},
        ]
    }
    resp = client.put(_overrides_url(fake_id), json=payload)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Bean not found."


def test_get_invalid_bean_id_returns_404(client):
    """GET with a nonexistent bean_id returns 404."""
    fake_id = str(uuid.uuid4())
    resp = client.get(_overrides_url(fake_id))
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Bean not found."
