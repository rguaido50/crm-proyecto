from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from crm.core.errors import NotFoundError, ValidationError
from crm.opportunities.models import Opportunity, OpportunityStage, OpportunityStatus
from crm.opportunities.schemas import OpportunityCreate, OpportunityUpdate


class OpportunityNotFoundError(NotFoundError):
    pass


class OpportunityValidationError(ValidationError):
    pass


def _require_non_blank(field: str, value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise OpportunityValidationError(f"{field} cannot be empty")
    return stripped


async def create_opportunity(session: AsyncSession, data: OpportunityCreate) -> Opportunity:
    fields = data.model_dump()
    fields["title"] = _require_non_blank("title", fields["title"])
    fields["owner"] = _require_non_blank("owner", fields["owner"])
    opportunity = Opportunity(**fields)
    session.add(opportunity)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise OpportunityValidationError("invalid contact_id") from exc
    await session.refresh(opportunity)
    return opportunity


async def get_opportunity(session: AsyncSession, opportunity_id: int) -> Opportunity:
    opportunity = await session.get(Opportunity, opportunity_id)
    if opportunity is None:
        raise OpportunityNotFoundError(opportunity_id)
    return opportunity


async def list_open_by_stage(
    session: AsyncSession,
) -> dict[OpportunityStage, list[Opportunity]]:
    result = await session.execute(
        select(Opportunity)
        .options(joinedload(Opportunity.contact))
        .where(Opportunity.status == OpportunityStatus.OPEN)
        .order_by(Opportunity.created_at)
    )
    board: dict[OpportunityStage, list[Opportunity]] = {stage: [] for stage in OpportunityStage}
    for opportunity in result.scalars().all():
        board[opportunity.stage].append(opportunity)
    return board


async def list_for_contact(session: AsyncSession, contact_id: int) -> list[Opportunity]:
    result = await session.execute(
        select(Opportunity)
        .where(Opportunity.contact_id == contact_id)
        .order_by(Opportunity.created_at)
    )
    return list(result.scalars().all())


async def update_opportunity(
    session: AsyncSession, opportunity_id: int, data: OpportunityUpdate
) -> Opportunity:
    opportunity = await get_opportunity(session, opportunity_id)
    updates = data.model_dump(exclude_unset=True)
    if "title" in updates:
        updates["title"] = _require_non_blank("title", updates["title"])
    if "owner" in updates:
        updates["owner"] = _require_non_blank("owner", updates["owner"])

    new_status = updates.get("status")
    if new_status is not None and new_status != opportunity.status:
        if new_status == OpportunityStatus.OPEN:
            opportunity.closed_at = None
        elif opportunity.status == OpportunityStatus.OPEN:
            opportunity.closed_at = func.now()

    for field, value in updates.items():
        setattr(opportunity, field, value)
    await session.commit()
    await session.refresh(opportunity)
    return opportunity
