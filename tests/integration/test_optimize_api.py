"""Tests for optimization seed data and campaign CRUD endpoints."""

import uuid

from sqlmodel import select

from beanbay.models.optimization import MethodParameterDefault
from beanbay.models.tag import BrewMethod
from beanbay.seed import seed_brew_methods
from beanbay.seed_optimization import seed_method_parameter_defaults


def test_seed_espresso_defaults(session):
    """Espresso defaults are seeded with the correct parameters."""
    seed_brew_methods(session)
    session.commit()
    seed_method_parameter_defaults(session)
    session.commit()

    espresso = session.exec(
        select(BrewMethod).where(BrewMethod.name == "espresso")
    ).one()

    defaults = session.exec(
        select(MethodParameterDefault).where(
            MethodParameterDefault.brew_method_id == espresso.id
        )
    ).all()

    param_names = {d.parameter_name for d in defaults}
    assert len(defaults) == 12
    assert param_names == {
        "temperature",
        "dose",
        "yield_amount",
        "pre_infusion_time",
        "preinfusion_pressure",
        "pressure",
        "flow_rate",
        "saturation",
        "bloom_pause",
        "pressure_profile",
        "brew_mode",
        "temp_profile",
    }
    # grind_setting must never be seeded
    assert "grind_setting" not in param_names

    # Spot-check a numeric parameter
    temp = next(d for d in defaults if d.parameter_name == "temperature")
    assert temp.min_value == 85.0
    assert temp.max_value == 105.0
    assert temp.step == 0.5
    assert temp.requires is None
    assert temp.allowed_values is None

    # Spot-check a categorical parameter
    pp = next(d for d in defaults if d.parameter_name == "pressure_profile")
    assert pp.min_value is None
    assert pp.max_value is None
    assert pp.step is None
    assert pp.allowed_values == "ramp_up,flat,decline,custom"
    assert pp.requires == "pressure_control_type in (manual_profiling, programmable)"


def test_seed_method_parameter_defaults_idempotent(session):
    """Running the seed function twice does not duplicate rows."""
    seed_brew_methods(session)
    session.commit()

    seed_method_parameter_defaults(session)
    session.commit()
    seed_method_parameter_defaults(session)
    session.commit()

    all_defaults = session.exec(select(MethodParameterDefault)).all()
    # 12 espresso + 4 pour-over + 4 french-press + 5 aeropress
    # + 3 turkish + 3 moka-pot + 3 cold-brew = 34 total
    assert len(all_defaults) == 34


def test_seed_all_methods_have_defaults(session):
    """Every brew method gets at least one parameter default."""
    seed_brew_methods(session)
    session.commit()
    seed_method_parameter_defaults(session)
    session.commit()

    methods = session.exec(select(BrewMethod)).all()
    for method in methods:
        defaults = session.exec(
            select(MethodParameterDefault).where(
                MethodParameterDefault.brew_method_id == method.id
            )
        ).all()
        assert len(defaults) > 0, f"No defaults seeded for {method.name}"


def test_seed_skips_missing_method(session):
    """If a brew method does not exist, seeding does not fail."""
    # Don't seed brew methods first — the function should silently skip
    seed_method_parameter_defaults(session)
    session.commit()

    all_defaults = session.exec(select(MethodParameterDefault)).all()
    assert len(all_defaults) == 0


# ---------------------------------------------------------------------------
# Helpers for campaign endpoint tests
# ---------------------------------------------------------------------------

CAMPAIGNS = "/api/v1/optimize/campaigns"
BEANS = "/api/v1/beans"
BREW_SETUPS = "/api/v1/brew-setups"
BREW_METHODS = "/api/v1/brew-methods"
DEFAULTS = "/api/v1/optimize/defaults"


def _create_brew_method(client, name: str = "espresso") -> str:
    """Create a brew method and return its id."""
    resp = client.post(BREW_METHODS, json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_bean(client, name: str = "Test Bean") -> str:
    """Create a bean and return its id."""
    resp = client.post(BEANS, json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_brew_setup(client, brew_method_id: str, **kwargs) -> str:
    """Create a brew setup and return its id."""
    payload = {"brew_method_id": brew_method_id, **kwargs}
    resp = client.post(BREW_SETUPS, json=payload)
    assert resp.status_code == 201
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Campaign CRUD tests
# ---------------------------------------------------------------------------


class TestCampaignCreate:
    """Tests for POST /api/v1/optimize/campaigns."""

    def test_create_campaign(self, client, session):
        """POST creates a new campaign for a valid bean + setup pair -> 201."""
        seed_brew_methods(session)
        session.commit()
        seed_method_parameter_defaults(session)
        session.commit()

        method_id = _create_brew_method(client, "espresso_camp1")
        bean_id = _create_bean(client, "Campaign Bean 1")
        setup_id = _create_brew_setup(client, method_id)

        resp = client.post(
            CAMPAIGNS,
            json={"bean_id": bean_id, "brew_setup_id": setup_id},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["bean_id"] == bean_id
        assert data["brew_setup_id"] == setup_id
        assert data["phase"] == "random"
        assert data["measurement_count"] == 0
        assert data["best_score"] is None
        assert "effective_ranges" in data

    def test_create_campaign_idempotent(self, client, session):
        """POST with same bean+setup returns existing campaign -> 200."""
        seed_brew_methods(session)
        session.commit()
        seed_method_parameter_defaults(session)
        session.commit()

        method_id = _create_brew_method(client, "espresso_camp2")
        bean_id = _create_bean(client, "Idempotent Bean")
        setup_id = _create_brew_setup(client, method_id)

        resp1 = client.post(
            CAMPAIGNS,
            json={"bean_id": bean_id, "brew_setup_id": setup_id},
        )
        assert resp1.status_code == 201
        campaign_id = resp1.json()["id"]

        resp2 = client.post(
            CAMPAIGNS,
            json={"bean_id": bean_id, "brew_setup_id": setup_id},
        )
        assert resp2.status_code == 200
        assert resp2.json()["id"] == campaign_id

    def test_create_campaign_invalid_bean(self, client):
        """POST with non-existent bean_id -> 404."""
        method_id = _create_brew_method(client, "espresso_camp3")
        setup_id = _create_brew_setup(client, method_id)
        fake_bean = str(uuid.uuid4())

        resp = client.post(
            CAMPAIGNS,
            json={"bean_id": fake_bean, "brew_setup_id": setup_id},
        )
        assert resp.status_code == 404
        assert "Bean" in resp.json()["detail"]

    def test_create_campaign_invalid_setup(self, client):
        """POST with non-existent brew_setup_id -> 404."""
        bean_id = _create_bean(client, "No Setup Bean")
        fake_setup = str(uuid.uuid4())

        resp = client.post(
            CAMPAIGNS,
            json={"bean_id": bean_id, "brew_setup_id": fake_setup},
        )
        assert resp.status_code == 404
        assert "BrewSetup" in resp.json()["detail"]


class TestCampaignList:
    """Tests for GET /api/v1/optimize/campaigns."""

    def test_list_campaigns(self, client, session):
        """GET returns all campaigns."""
        seed_brew_methods(session)
        session.commit()
        seed_method_parameter_defaults(session)
        session.commit()

        method_id = _create_brew_method(client, "espresso_list1")
        bean_id = _create_bean(client, "List Bean")
        setup_id = _create_brew_setup(client, method_id)

        client.post(
            CAMPAIGNS,
            json={"bean_id": bean_id, "brew_setup_id": setup_id},
        )

        resp = client.get(CAMPAIGNS)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_campaigns_filter_bean(self, client, session):
        """GET with bean_id filter narrows results."""
        seed_brew_methods(session)
        session.commit()
        seed_method_parameter_defaults(session)
        session.commit()

        method_id = _create_brew_method(client, "espresso_flt1")
        bean1_id = _create_bean(client, "Filter Bean A")
        bean2_id = _create_bean(client, "Filter Bean B")
        setup_id = _create_brew_setup(client, method_id)

        client.post(
            CAMPAIGNS,
            json={"bean_id": bean1_id, "brew_setup_id": setup_id},
        )
        client.post(
            CAMPAIGNS,
            json={"bean_id": bean2_id, "brew_setup_id": setup_id},
        )

        resp = client.get(CAMPAIGNS, params={"bean_id": bean1_id})
        assert resp.status_code == 200
        data = resp.json()
        assert all(c["bean_name"] == "Filter Bean A" for c in data)

    def test_list_campaigns_filter_setup(self, client, session):
        """GET with brew_setup_id filter narrows results."""
        seed_brew_methods(session)
        session.commit()
        seed_method_parameter_defaults(session)
        session.commit()

        method_id = _create_brew_method(client, "espresso_flt2")
        bean_id = _create_bean(client, "Setup Filter Bean")
        setup1_id = _create_brew_setup(client, method_id, name="Setup A")
        setup2_id = _create_brew_setup(client, method_id, name="Setup B")

        client.post(
            CAMPAIGNS,
            json={"bean_id": bean_id, "brew_setup_id": setup1_id},
        )
        client.post(
            CAMPAIGNS,
            json={"bean_id": bean_id, "brew_setup_id": setup2_id},
        )

        resp = client.get(CAMPAIGNS, params={"brew_setup_id": setup1_id})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1


class TestCampaignDetail:
    """Tests for GET /api/v1/optimize/campaigns/{id}."""

    def test_get_campaign_detail(self, client, session):
        """GET returns campaign with effective_ranges."""
        seed_brew_methods(session)
        session.commit()
        seed_method_parameter_defaults(session)
        session.commit()

        method_id = _create_brew_method(client, "espresso_det1")
        bean_id = _create_bean(client, "Detail Bean")
        setup_id = _create_brew_setup(client, method_id)

        resp = client.post(
            CAMPAIGNS,
            json={"bean_id": bean_id, "brew_setup_id": setup_id},
        )
        campaign_id = resp.json()["id"]

        resp = client.get(f"{CAMPAIGNS}/{campaign_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == campaign_id
        assert "effective_ranges" in data

    def test_get_campaign_not_found(self, client):
        """GET with invalid id -> 404."""
        fake_id = str(uuid.uuid4())
        resp = client.get(f"{CAMPAIGNS}/{fake_id}")
        assert resp.status_code == 404


class TestCampaignReset:
    """Tests for DELETE /api/v1/optimize/campaigns/{id}."""

    def test_reset_campaign(self, client, session):
        """DELETE resets campaign state."""
        seed_brew_methods(session)
        session.commit()
        seed_method_parameter_defaults(session)
        session.commit()

        method_id = _create_brew_method(client, "espresso_rst1")
        bean_id = _create_bean(client, "Reset Bean")
        setup_id = _create_brew_setup(client, method_id)

        resp = client.post(
            CAMPAIGNS,
            json={"bean_id": bean_id, "brew_setup_id": setup_id},
        )
        campaign_id = resp.json()["id"]

        resp = client.delete(f"{CAMPAIGNS}/{campaign_id}")
        assert resp.status_code == 200
        assert resp.json()["detail"] == "Campaign reset."

    def test_reset_campaign_not_found(self, client):
        """DELETE with invalid id -> 404."""
        fake_id = str(uuid.uuid4())
        resp = client.delete(f"{CAMPAIGNS}/{fake_id}")
        assert resp.status_code == 404


class TestMethodDefaults:
    """Tests for GET /api/v1/optimize/defaults/{brew_method_id}."""

    def test_get_method_defaults(self, client, session):
        """GET returns parameter defaults for a brew method."""
        seed_brew_methods(session)
        session.commit()
        seed_method_parameter_defaults(session)
        session.commit()

        # Find espresso method id
        espresso = session.exec(
            select(BrewMethod).where(BrewMethod.name == "espresso")
        ).one()

        resp = client.get(f"{DEFAULTS}/{espresso.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 12
        param_names = {d["parameter_name"] for d in data}
        assert "temperature" in param_names

    def test_get_method_defaults_not_found(self, client):
        """GET with invalid brew_method_id -> 404."""
        fake_id = str(uuid.uuid4())
        resp = client.get(f"{DEFAULTS}/{fake_id}")
        assert resp.status_code == 404
