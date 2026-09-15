from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from crm.opportunities.models import OpportunityStage, OpportunityStatus


class OpportunityCreate(BaseModel):
    contact_id: int
    title: str
    value_usd: Decimal | None = None
    stage: OpportunityStage = OpportunityStage.NEW
    status: OpportunityStatus = OpportunityStatus.OPEN
    expected_close_date: date | None = None
    owner: str


class OpportunityUpdate(BaseModel):
    title: str | None = None
    value_usd: Decimal | None = None
    stage: OpportunityStage | None = None
    status: OpportunityStatus | None = None
    expected_close_date: date | None = None
    owner: str | None = None


class OpportunityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contact_id: int
    title: str
    value_usd: Decimal | None
    stage: OpportunityStage
    status: OpportunityStatus
    expected_close_date: date | None
    closed_at: datetime | None
    owner: str
    created_at: datetime
    updated_at: datetime
