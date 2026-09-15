from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from crm.core.db import get_session
from crm.opportunities import service
from crm.opportunities.models import Opportunity
from crm.opportunities.schemas import OpportunityCreate, OpportunityRead, OpportunityUpdate

router = APIRouter(prefix="/api/opportunities", tags=["opportunities"])


@router.post("", response_model=OpportunityRead, status_code=201)
async def create_opportunity(
    data: OpportunityCreate, session: AsyncSession = Depends(get_session)
) -> Opportunity:
    return await service.create_opportunity(session, data)


@router.get("", response_model=dict[str, list[OpportunityRead]])
async def list_open_by_stage(
    session: AsyncSession = Depends(get_session),
) -> dict[str, list[Opportunity]]:
    board = await service.list_open_by_stage(session)
    return {stage.value: opportunities for stage, opportunities in board.items()}


@router.get("/{opportunity_id}", response_model=OpportunityRead)
async def get_opportunity(
    opportunity_id: int, session: AsyncSession = Depends(get_session)
) -> Opportunity:
    return await service.get_opportunity(session, opportunity_id)


@router.patch("/{opportunity_id}", response_model=OpportunityRead)
async def update_opportunity(
    opportunity_id: int,
    data: OpportunityUpdate,
    session: AsyncSession = Depends(get_session),
) -> Opportunity:
    return await service.update_opportunity(session, opportunity_id, data)
