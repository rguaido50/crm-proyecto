from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from crm.core.db import get_session
from crm.opportunities.models import OpportunityStage
from crm.reports import service
from crm.reports.schemas import FunnelReport, MonthlyWonLost, PipelineStageReport

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/pipeline", response_model=dict[OpportunityStage, PipelineStageReport])
async def pipeline(
    session: AsyncSession = Depends(get_session),
) -> dict[OpportunityStage, PipelineStageReport]:
    return await service.pipeline_by_stage(session)


@router.get("/won-lost", response_model=list[MonthlyWonLost])
async def won_lost(session: AsyncSession = Depends(get_session)) -> list[MonthlyWonLost]:
    return await service.won_lost_by_month(session)


@router.get("/funnel", response_model=FunnelReport)
async def funnel(session: AsyncSession = Depends(get_session)) -> FunnelReport:
    return await service.conversion_funnel(session)
