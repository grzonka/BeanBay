"""Router for optimization endpoints.

Provides bean parameter override management, campaign CRUD, and
method parameter default queries.
"""

import uuid

from fastapi import APIRouter, HTTPException, Query, Response
from sqlmodel import select

from beanbay.dependencies import SessionDep
from beanbay.models.bean import Bean
from beanbay.models.brew import BrewSetup
from beanbay.models.equipment import Brewer, Grinder
from beanbay.models.optimization import (
    BeanParameterOverride,
    Campaign,
    MethodParameterDefault,
    Recommendation,
)
from beanbay.models.tag import BrewMethod
from beanbay.schemas.optimization import (
    BeanOverrideRead,
    BeanOverridesPut,
    CampaignCreate,
    CampaignDetailRead,
    CampaignListRead,
    EffectiveRange,
    MethodParameterDefaultRead,
)
from beanbay.services.parameter_ranges import compute_effective_ranges

router = APIRouter(tags=["Optimization"])


@router.get(
    "/optimize/beans/{bean_id}/overrides",
    response_model=list[BeanOverrideRead],
)
def list_bean_overrides(
    bean_id: uuid.UUID,
    session: SessionDep,
) -> list[BeanOverrideRead]:
    """List parameter overrides for a bean.

    Parameters
    ----------
    bean_id : uuid.UUID
        Primary key of the bean.
    session : SessionDep
        Database session.

    Returns
    -------
    list[BeanOverrideRead]
        All parameter overrides for the given bean.

    Raises
    ------
    HTTPException
        404 if the bean does not exist.
    """
    bean = session.get(Bean, bean_id)
    if bean is None:
        raise HTTPException(status_code=404, detail="Bean not found.")
    overrides = session.exec(
        select(BeanParameterOverride).where(
            BeanParameterOverride.bean_id == bean_id
        )
    ).all()
    return overrides  # type: ignore[return-value]


@router.put(
    "/optimize/beans/{bean_id}/overrides",
    response_model=list[BeanOverrideRead],
)
def put_bean_overrides(
    bean_id: uuid.UUID,
    payload: BeanOverridesPut,
    session: SessionDep,
) -> list[BeanOverrideRead]:
    """Set/replace all parameter overrides for a bean.

    Deletes any existing overrides for the bean and inserts the new set.
    Passing an empty list clears all overrides.

    Parameters
    ----------
    bean_id : uuid.UUID
        Primary key of the bean.
    payload : BeanOverridesPut
        The override items to set.
    session : SessionDep
        Database session.

    Returns
    -------
    list[BeanOverrideRead]
        The newly created overrides.

    Raises
    ------
    HTTPException
        404 if the bean does not exist.
    """
    bean = session.get(Bean, bean_id)
    if bean is None:
        raise HTTPException(status_code=404, detail="Bean not found.")

    # Delete existing overrides
    existing = session.exec(
        select(BeanParameterOverride).where(
            BeanParameterOverride.bean_id == bean_id
        )
    ).all()
    for override in existing:
        session.delete(override)
    session.flush()

    # Insert new overrides
    new_overrides = []
    for item in payload.overrides:
        db_override = BeanParameterOverride(
            bean_id=bean_id,
            parameter_name=item.parameter_name,
            min_value=item.min_value,
            max_value=item.max_value,
        )
        session.add(db_override)
        new_overrides.append(db_override)

    session.commit()
    for o in new_overrides:
        session.refresh(o)
    return new_overrides  # type: ignore[return-value]


# ======================================================================
# Campaign CRUD
# ======================================================================


def _compute_campaign_ranges(
    session,
    campaign: Campaign,
) -> list[EffectiveRange]:
    """Compute effective parameter ranges for a campaign.

    Parameters
    ----------
    session : Session
        Database session.
    campaign : Campaign
        The campaign to compute ranges for.

    Returns
    -------
    list[EffectiveRange]
        Effective ranges converted to schema objects.
    """
    setup = session.get(BrewSetup, campaign.brew_setup_id)

    # Load method defaults
    defaults = session.exec(
        select(MethodParameterDefault).where(
            MethodParameterDefault.brew_method_id == setup.brew_method_id
        )
    ).all()

    # Load equipment (may be None)
    brewer = session.get(Brewer, setup.brewer_id) if setup.brewer_id else None
    grinder = (
        session.get(Grinder, setup.grinder_id) if setup.grinder_id else None
    )

    # Load bean overrides
    overrides = session.exec(
        select(BeanParameterOverride).where(
            BeanParameterOverride.bean_id == campaign.bean_id
        )
    ).all()

    service_ranges = compute_effective_ranges(
        defaults, brewer, grinder, overrides
    )

    # Convert dataclasses to schema objects
    return [
        EffectiveRange(
            parameter_name=r.parameter_name,
            min_value=r.min_value,
            max_value=r.max_value,
            step=r.step,
            allowed_values=r.allowed_values,
            source=r.source,
        )
        for r in service_ranges
    ]


def _campaign_to_detail(
    session,
    campaign: Campaign,
) -> CampaignDetailRead:
    """Build a CampaignDetailRead from a Campaign model.

    Parameters
    ----------
    session : Session
        Database session.
    campaign : Campaign
        The campaign model.

    Returns
    -------
    CampaignDetailRead
        Full detail schema with effective ranges.
    """
    bean = session.get(Bean, campaign.bean_id)
    setup = session.get(BrewSetup, campaign.brew_setup_id)

    ranges = _compute_campaign_ranges(session, campaign)

    return CampaignDetailRead(
        id=campaign.id,
        bean_id=campaign.bean_id,
        brew_setup_id=campaign.brew_setup_id,
        phase=campaign.phase,
        measurement_count=campaign.measurement_count,
        best_score=campaign.best_score,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
        bean_name=bean.name if bean else None,
        brew_setup_name=setup.name if setup else None,
        effective_ranges=ranges,
    )


@router.post(
    "/optimize/campaigns",
    response_model=CampaignDetailRead,
    status_code=201,
)
def create_or_get_campaign(
    payload: CampaignCreate,
    response: Response,
    session: SessionDep,
) -> CampaignDetailRead:
    """Create a campaign or return existing one for this bean+setup.

    If a campaign already exists for the given bean and brew setup
    combination, the existing campaign is returned with status 200
    instead of 201.

    Parameters
    ----------
    payload : CampaignCreate
        Bean and brew setup IDs.
    response : Response
        FastAPI response object for status code override.
    session : SessionDep
        Database session.

    Returns
    -------
    CampaignDetailRead
        The created or existing campaign with effective ranges.

    Raises
    ------
    HTTPException
        404 if bean or brew setup does not exist.
    """
    # Validate bean_id
    bean = session.get(Bean, payload.bean_id)
    if bean is None:
        raise HTTPException(status_code=404, detail="Bean not found.")

    # Validate brew_setup_id
    setup = session.get(BrewSetup, payload.brew_setup_id)
    if setup is None:
        raise HTTPException(status_code=404, detail="BrewSetup not found.")

    # Check for existing campaign
    existing = session.exec(
        select(Campaign).where(
            Campaign.bean_id == payload.bean_id,
            Campaign.brew_setup_id == payload.brew_setup_id,
        )
    ).first()

    if existing is not None:
        response.status_code = 200
        return _campaign_to_detail(session, existing)

    # Create new campaign
    campaign = Campaign(
        bean_id=payload.bean_id,
        brew_setup_id=payload.brew_setup_id,
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)

    return _campaign_to_detail(session, campaign)


@router.get(
    "/optimize/campaigns",
    response_model=list[CampaignListRead],
)
def list_campaigns(
    bean_id: uuid.UUID | None = Query(None),
    brew_setup_id: uuid.UUID | None = Query(None),
    *,
    session: SessionDep,
) -> list[CampaignListRead]:
    """List campaigns with optional filters.

    Parameters
    ----------
    bean_id : uuid.UUID | None
        Filter by bean ID.
    brew_setup_id : uuid.UUID | None
        Filter by brew setup ID.
    session : SessionDep
        Database session.

    Returns
    -------
    list[CampaignListRead]
        Summary list of matching campaigns.
    """
    stmt = select(Campaign)

    if bean_id is not None:
        stmt = stmt.where(Campaign.bean_id == bean_id)
    if brew_setup_id is not None:
        stmt = stmt.where(Campaign.brew_setup_id == brew_setup_id)

    campaigns = session.exec(stmt).all()

    results = []
    for campaign in campaigns:
        bean = session.get(Bean, campaign.bean_id)
        setup = session.get(BrewSetup, campaign.brew_setup_id)
        results.append(
            CampaignListRead(
                id=campaign.id,
                bean_name=bean.name if bean else None,
                brew_setup_name=setup.name if setup else None,
                phase=campaign.phase,
                measurement_count=campaign.measurement_count,
                best_score=campaign.best_score,
                created_at=campaign.created_at,
            )
        )

    return results


@router.get(
    "/optimize/campaigns/{campaign_id}",
    response_model=CampaignDetailRead,
)
def get_campaign(
    campaign_id: uuid.UUID,
    session: SessionDep,
) -> CampaignDetailRead:
    """Get campaign detail with effective parameter ranges.

    Parameters
    ----------
    campaign_id : uuid.UUID
        Primary key of the campaign.
    session : SessionDep
        Database session.

    Returns
    -------
    CampaignDetailRead
        Campaign with effective ranges.

    Raises
    ------
    HTTPException
        404 if the campaign does not exist.
    """
    campaign = session.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    return _campaign_to_detail(session, campaign)


@router.delete("/optimize/campaigns/{campaign_id}")
def reset_campaign(
    campaign_id: uuid.UUID,
    session: SessionDep,
) -> dict:
    """Reset campaign: clear BayBE state, keep brew records.

    Sets ``campaign_json`` to None, ``phase`` to ``"random"``,
    ``measurement_count`` to 0, ``best_score`` to None. Deletes
    related recommendations and clears fingerprints.

    Parameters
    ----------
    campaign_id : uuid.UUID
        Primary key of the campaign.
    session : SessionDep
        Database session.

    Returns
    -------
    dict
        Confirmation message.

    Raises
    ------
    HTTPException
        404 if the campaign does not exist.
    """
    campaign = session.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    # Reset campaign state
    campaign.campaign_json = None
    campaign.phase = "random"
    campaign.measurement_count = 0
    campaign.best_score = None
    campaign.bounds_fingerprint = None
    campaign.param_fingerprint = None

    # Delete related recommendations
    recommendations = session.exec(
        select(Recommendation).where(
            Recommendation.campaign_id == campaign_id
        )
    ).all()
    for rec in recommendations:
        session.delete(rec)

    session.add(campaign)
    session.commit()

    return {"detail": "Campaign reset."}


# ======================================================================
# Method Parameter Defaults
# ======================================================================


@router.get(
    "/optimize/defaults/{brew_method_id}",
    response_model=list[MethodParameterDefaultRead],
)
def get_method_defaults(
    brew_method_id: uuid.UUID,
    session: SessionDep,
) -> list[MethodParameterDefaultRead]:
    """Get parameter defaults for a brew method.

    Parameters
    ----------
    brew_method_id : uuid.UUID
        Primary key of the brew method.
    session : SessionDep
        Database session.

    Returns
    -------
    list[MethodParameterDefaultRead]
        All parameter defaults for the given brew method.

    Raises
    ------
    HTTPException
        404 if the brew method does not exist.
    """
    method = session.get(BrewMethod, brew_method_id)
    if method is None:
        raise HTTPException(status_code=404, detail="BrewMethod not found.")

    defaults = session.exec(
        select(MethodParameterDefault).where(
            MethodParameterDefault.brew_method_id == brew_method_id
        )
    ).all()

    return defaults  # type: ignore[return-value]
