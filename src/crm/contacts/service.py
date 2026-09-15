from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts.models import Contact
from crm.contacts.schemas import ContactCreate


class ContactNotFoundError(Exception):
    pass


async def create_contact(session: AsyncSession, data: ContactCreate) -> Contact:
    contact = Contact(**data.model_dump())
    session.add(contact)
    await session.commit()
    await session.refresh(contact)
    return contact


async def get_contact(session: AsyncSession, contact_id: int) -> Contact:
    contact = await session.get(Contact, contact_id)
    if contact is None:
        raise ContactNotFoundError(contact_id)
    return contact
