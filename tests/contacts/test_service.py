from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts import service
from crm.contacts.schemas import ContactCreate


async def test_create_contact_persists_the_given_fields(session: AsyncSession) -> None:
    contact = await service.create_contact(
        session,
        ContactCreate(name="Ada Lovelace", company="Acme", email="ada@acme.com"),
    )

    assert contact.id is not None
    assert contact.name == "Ada Lovelace"
    assert contact.company == "Acme"
    assert contact.email == "ada@acme.com"
