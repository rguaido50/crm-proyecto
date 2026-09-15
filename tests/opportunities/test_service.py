from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts import service as contacts_service
from crm.contacts.schemas import ContactCreate
from crm.opportunities import service
from crm.opportunities.schemas import OpportunityCreate


async def test_create_opportunity_persists_the_given_fields(session: AsyncSession) -> None:
    contact = await contacts_service.create_contact(session, ContactCreate(name="Ada Lovelace"))

    opportunity = await service.create_opportunity(
        session,
        OpportunityCreate(contact_id=contact.id, title="itela support contract", owner="Sam"),
    )

    assert opportunity.id is not None
    assert opportunity.contact_id == contact.id
    assert opportunity.title == "itela support contract"
    assert opportunity.owner == "Sam"
