from decimal import Decimal

from pydantic import BaseModel

from crm.opportunities.models import OpportunityStage


class PipelineStageReport(BaseModel):
    stage: OpportunityStage
    total: Decimal
    count: int
    unvalued_count: int


class MonthlyWonLost(BaseModel):
    label: str
    won_total: Decimal
    lost_total: Decimal
    won_count: int
    lost_count: int


class FunnelStage(BaseModel):
    stage: OpportunityStage
    count: int
    percentage: Decimal


class FunnelReport(BaseModel):
    stages: list[FunnelStage]
    win_rate: Decimal | None
