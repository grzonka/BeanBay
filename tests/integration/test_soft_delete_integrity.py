"""Integration tests for soft-delete referential integrity (409 Conflict).

Verifies that lookup entities referenced by active records cannot be
soft-deleted, while lookup entities whose references are all retired
can be deleted successfully.  Also verifies that Person soft-delete is
always permitted regardless of active references.
"""

import uuid
from datetime import datetime, timezone

# ======================================================================
# API base URLs
# ======================================================================
ORIGINS = "/api/v1/origins"
ROASTERS = "/api/v1/roasters"
PROCESS_METHODS = "/api/v1/process-methods"
BEAN_VARIETIES = "/api/v1/bean-varieties"
FLAVOR_TAGS = "/api/v1/flavor-tags"
BREW_METHODS = "/api/v1/brew-methods"
STOP_MODES = "/api/v1/stop-modes"
BEANS = "/api/v1/beans"
BREW_SETUPS = "/api/v1/brew-setups"
BREWS = "/api/v1/brews"
BREWERS = "/api/v1/brewers"
PEOPLE = "/api/v1/people"
BEAN_RATINGS = "/api/v1/bean-ratings"


# ======================================================================
# Helpers
# ======================================================================


def _unique(prefix: str) -> str:
    """Return a unique name to avoid collisions across tests."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _create_origin(client, name=None) -> str:
    name = name or _unique("origin")
    resp = client.post(ORIGINS, json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_roaster(client, name=None) -> str:
    name = name or _unique("roaster")
    resp = client.post(ROASTERS, json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_process_method(client, name=None) -> str:
    name = name or _unique("process")
    resp = client.post(PROCESS_METHODS, json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_bean_variety(client, name=None) -> str:
    name = name or _unique("variety")
    resp = client.post(BEAN_VARIETIES, json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_flavor_tag(client, name=None) -> str:
    name = name or _unique("tag")
    resp = client.post(FLAVOR_TAGS, json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_brew_method(client, name=None) -> str:
    name = name or _unique("method")
    resp = client.post(BREW_METHODS, json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_stop_mode(client, name=None) -> str:
    name = name or _unique("stop")
    resp = client.post(STOP_MODES, json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_bean(client, name=None, **kwargs) -> dict:
    name = name or _unique("bean")
    payload = {"name": name, **kwargs}
    resp = client.post(BEANS, json=payload)
    assert resp.status_code == 201
    return resp.json()


def _create_bag(client, bean_id: str) -> str:
    resp = client.post(f"{BEANS}/{bean_id}/bags", json={"weight": 250.0})
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_person(client, name=None) -> str:
    name = name or _unique("person")
    resp = client.post(PEOPLE, json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_brew_setup(client, brew_method_id: str, **kwargs) -> str:
    payload = {"brew_method_id": brew_method_id, **kwargs}
    resp = client.post(BREW_SETUPS, json=payload)
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_brewer(client, name=None, **kwargs) -> str:
    name = name or _unique("brewer")
    payload = {"name": name, **kwargs}
    resp = client.post(BREWERS, json=payload)
    assert resp.status_code == 201
    return resp.json()["id"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _create_brew(
    client,
    bag_id: str,
    brew_setup_id: str,
    person_id: str,
    **kwargs,
) -> dict:
    payload = {
        "bag_id": bag_id,
        "brew_setup_id": brew_setup_id,
        "person_id": person_id,
        "dose": 18.0,
        "brewed_at": _now_iso(),
        **kwargs,
    }
    resp = client.post(BREWS, json=payload)
    assert resp.status_code == 201
    return resp.json()


def _create_rating(client, bean_id: str, person_id: str, **kwargs) -> dict:
    payload = {"person_id": person_id, **kwargs}
    resp = client.post(f"{BEANS}/{bean_id}/ratings", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ======================================================================
# 1. Origin — M2M via BeanOriginLink
# ======================================================================


class TestOriginSoftDeleteIntegrity:
    """Origin cannot be retired while active beans reference it."""

    def test_cannot_delete_origin_linked_to_active_bean(self, client):
        """DELETE /origins/{id} returns 409 when an active bean uses it."""
        origin_id = _create_origin(client)
        _create_bean(client, origin_ids=[origin_id])

        resp = client.delete(f"{ORIGINS}/{origin_id}")
        assert resp.status_code == 409
        assert "active reference" in resp.json()["detail"]

    def test_can_delete_origin_after_bean_retired(self, client):
        """DELETE /origins/{id} succeeds once the referencing bean is retired."""
        origin_id = _create_origin(client)
        bean = _create_bean(client, origin_ids=[origin_id])
        bean_id = bean["id"]

        # Retire the bean (must retire bags first — none here)
        resp = client.delete(f"{BEANS}/{bean_id}")
        assert resp.status_code == 200

        # Now the origin can be retired
        resp = client.delete(f"{ORIGINS}/{origin_id}")
        assert resp.status_code == 200
        assert resp.json()["retired_at"] is not None

    def test_can_delete_unreferenced_origin(self, client):
        """DELETE /origins/{id} succeeds when no beans reference it."""
        origin_id = _create_origin(client)
        resp = client.delete(f"{ORIGINS}/{origin_id}")
        assert resp.status_code == 200


# ======================================================================
# 2. Roaster — direct FK from Bean
# ======================================================================


class TestRoasterSoftDeleteIntegrity:
    """Roaster cannot be retired while active beans reference it."""

    def test_cannot_delete_roaster_linked_to_active_bean(self, client):
        """DELETE /roasters/{id} returns 409 when an active bean uses it."""
        roaster_id = _create_roaster(client)
        _create_bean(client, roaster_id=roaster_id)

        resp = client.delete(f"{ROASTERS}/{roaster_id}")
        assert resp.status_code == 409
        assert "active reference" in resp.json()["detail"]

    def test_can_delete_roaster_after_bean_retired(self, client):
        """DELETE /roasters/{id} succeeds once the referencing bean is retired."""
        roaster_id = _create_roaster(client)
        bean = _create_bean(client, roaster_id=roaster_id)
        bean_id = bean["id"]

        resp = client.delete(f"{BEANS}/{bean_id}")
        assert resp.status_code == 200

        resp = client.delete(f"{ROASTERS}/{roaster_id}")
        assert resp.status_code == 200
        assert resp.json()["retired_at"] is not None


# ======================================================================
# 3. ProcessMethod — M2M via BeanProcessLink
# ======================================================================


class TestProcessMethodSoftDeleteIntegrity:
    """ProcessMethod cannot be retired while active beans reference it."""

    def test_cannot_delete_process_method_linked_to_active_bean(self, client):
        """DELETE /process-methods/{id} returns 409."""
        pm_id = _create_process_method(client)
        _create_bean(client, process_ids=[pm_id])

        resp = client.delete(f"{PROCESS_METHODS}/{pm_id}")
        assert resp.status_code == 409

    def test_can_delete_process_method_after_bean_retired(self, client):
        """Succeeds once the bean is retired."""
        pm_id = _create_process_method(client)
        bean = _create_bean(client, process_ids=[pm_id])

        client.delete(f"{BEANS}/{bean['id']}")

        resp = client.delete(f"{PROCESS_METHODS}/{pm_id}")
        assert resp.status_code == 200


# ======================================================================
# 4. BeanVariety — M2M via BeanVarietyLink
# ======================================================================


class TestBeanVarietySoftDeleteIntegrity:
    """BeanVariety cannot be retired while active beans reference it."""

    def test_cannot_delete_variety_linked_to_active_bean(self, client):
        """DELETE /bean-varieties/{id} returns 409."""
        var_id = _create_bean_variety(client)
        _create_bean(client, variety_ids=[var_id])

        resp = client.delete(f"{BEAN_VARIETIES}/{var_id}")
        assert resp.status_code == 409

    def test_can_delete_variety_after_bean_retired(self, client):
        """Succeeds once the bean is retired."""
        var_id = _create_bean_variety(client)
        bean = _create_bean(client, variety_ids=[var_id])

        client.delete(f"{BEANS}/{bean['id']}")

        resp = client.delete(f"{BEAN_VARIETIES}/{var_id}")
        assert resp.status_code == 200


# ======================================================================
# 5. FlavorTag — M2M via BrewTasteFlavorTagLink (through BrewTaste → Brew)
# ======================================================================


class TestFlavorTagSoftDeleteIntegrity:
    """FlavorTag cannot be retired while an active brew's taste uses it."""

    def test_cannot_delete_flavor_tag_linked_to_active_brew_taste(self, client):
        """DELETE /flavor-tags/{id} returns 409 when a non-retired brew uses it."""
        tag_id = _create_flavor_tag(client)

        # Set up a brew with a taste using this tag
        person_id = _create_person(client)
        bean = _create_bean(client)
        bag_id = _create_bag(client, bean["id"])
        method_id = _create_brew_method(client)
        setup_id = _create_brew_setup(client, method_id)
        _create_brew(
            client,
            bag_id,
            setup_id,
            person_id,
            taste={
                "score": 8.0,
                "flavor_tag_ids": [tag_id],
            },
        )

        resp = client.delete(f"{FLAVOR_TAGS}/{tag_id}")
        assert resp.status_code == 409
        assert "active reference" in resp.json()["detail"]

    def test_can_delete_flavor_tag_after_brew_retired(self, client):
        """DELETE /flavor-tags/{id} succeeds once the brew is retired."""
        tag_id = _create_flavor_tag(client)

        person_id = _create_person(client)
        bean = _create_bean(client)
        bag_id = _create_bag(client, bean["id"])
        method_id = _create_brew_method(client)
        setup_id = _create_brew_setup(client, method_id)
        brew = _create_brew(
            client,
            bag_id,
            setup_id,
            person_id,
            taste={
                "score": 8.0,
                "flavor_tag_ids": [tag_id],
            },
        )

        # Retire the brew
        resp = client.delete(f"{BREWS}/{brew['id']}")
        assert resp.status_code == 200

        # Now the tag can be retired
        resp = client.delete(f"{FLAVOR_TAGS}/{tag_id}")
        assert resp.status_code == 200
        assert resp.json()["retired_at"] is not None

    def test_cannot_delete_flavor_tag_linked_to_active_bean_rating_taste(self, client):
        """DELETE /flavor-tags/{id} returns 409 when a BeanRating taste uses it."""
        tag_id = _create_flavor_tag(client)

        person_id = _create_person(client)
        bean = _create_bean(client)

        # Create rating with taste + flavor tag
        _create_rating(
            client,
            bean["id"],
            person_id,
            taste={
                "score": 7.0,
                "flavor_tag_ids": [tag_id],
            },
        )

        resp = client.delete(f"{FLAVOR_TAGS}/{tag_id}")
        assert resp.status_code == 409

    def test_can_delete_flavor_tag_after_bean_rating_retired(self, client):
        """FlavorTag can be retired once its referencing bean rating is retired."""
        tag_id = _create_flavor_tag(client)

        person_id = _create_person(client)
        bean = _create_bean(client)

        rating = _create_rating(
            client,
            bean["id"],
            person_id,
            taste={
                "score": 7.0,
                "flavor_tag_ids": [tag_id],
            },
        )

        # Retire the rating
        resp = client.delete(f"{BEAN_RATINGS}/{rating['id']}")
        assert resp.status_code == 200

        # Now the tag can be retired
        resp = client.delete(f"{FLAVOR_TAGS}/{tag_id}")
        assert resp.status_code == 200


# ======================================================================
# 6. BrewMethod — direct FK from BrewSetup
# ======================================================================


class TestBrewMethodSoftDeleteIntegrity:
    """BrewMethod cannot be retired while active brew setups reference it."""

    def test_cannot_delete_brew_method_linked_to_active_setup(self, client):
        """DELETE /brew-methods/{id} returns 409."""
        method_id = _create_brew_method(client)
        _create_brew_setup(client, method_id)

        resp = client.delete(f"{BREW_METHODS}/{method_id}")
        assert resp.status_code == 409
        assert "active reference" in resp.json()["detail"]

    def test_can_delete_brew_method_after_setup_retired(self, client):
        """DELETE /brew-methods/{id} succeeds once the setup is retired."""
        method_id = _create_brew_method(client)
        setup_id = _create_brew_setup(client, method_id)

        # Retire the setup
        resp = client.delete(f"{BREW_SETUPS}/{setup_id}")
        assert resp.status_code == 200

        resp = client.delete(f"{BREW_METHODS}/{method_id}")
        assert resp.status_code == 200
        assert resp.json()["retired_at"] is not None


# ======================================================================
# 7. StopMode — M2M via BrewerStopModeLink + direct FK from Brew
# ======================================================================


class TestStopModeSoftDeleteIntegrity:
    """StopMode cannot be retired while active brewers or brews reference it."""

    def test_cannot_delete_stop_mode_linked_to_active_brewer(self, client):
        """DELETE /stop-modes/{id} returns 409 when a brewer uses it."""
        stop_id = _create_stop_mode(client)
        _create_brewer(client, stop_mode_ids=[stop_id])

        resp = client.delete(f"{STOP_MODES}/{stop_id}")
        assert resp.status_code == 409

    def test_cannot_delete_stop_mode_linked_to_active_brew(self, client):
        """DELETE /stop-modes/{id} returns 409 when a brew uses it."""
        stop_id = _create_stop_mode(client)

        person_id = _create_person(client)
        bean = _create_bean(client)
        bag_id = _create_bag(client, bean["id"])
        method_id = _create_brew_method(client)
        setup_id = _create_brew_setup(client, method_id)
        _create_brew(
            client,
            bag_id,
            setup_id,
            person_id,
            stop_mode_id=stop_id,
        )

        resp = client.delete(f"{STOP_MODES}/{stop_id}")
        assert resp.status_code == 409


# ======================================================================
# 8. Person — soft-delete ALLOWED even with active references
# ======================================================================


class TestPersonSoftDeleteAllowed:
    """Person soft-delete is allowed per spec, even with active brews."""

    def test_can_delete_person_with_active_brew(self, client):
        """DELETE /people/{id} returns 200 even if the person has active brews."""
        person_id = _create_person(client)
        bean = _create_bean(client)
        bag_id = _create_bag(client, bean["id"])
        method_id = _create_brew_method(client)
        setup_id = _create_brew_setup(client, method_id)
        _create_brew(client, bag_id, setup_id, person_id)

        resp = client.delete(f"{PEOPLE}/{person_id}")
        assert resp.status_code == 200
        assert resp.json()["retired_at"] is not None

    def test_can_delete_person_with_active_rating(self, client):
        """DELETE /people/{id} returns 200 even if the person has active ratings."""
        person_id = _create_person(client)
        bean = _create_bean(client)
        _create_rating(client, bean["id"], person_id)

        resp = client.delete(f"{PEOPLE}/{person_id}")
        assert resp.status_code == 200
        assert resp.json()["retired_at"] is not None
