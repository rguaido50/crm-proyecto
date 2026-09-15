from sqlalchemy.ext.asyncio import AsyncSession

from crm.core.errors import NotFoundError
from crm.opportunities.models import Opportunity
from crm.opportunities.schemas import OpportunityCreate


class OpportunityNotFoundError(NotFoundError):
    pass


async def create_opportunity(session: AsyncSession, data: OpportunityCreate) -> Opportunity:
    opportunity = Opportunity(**data.model_dump())
    session.add(opportunity)
    await session.commit()
    await session.refresh(opportunity)
    return opportunity
