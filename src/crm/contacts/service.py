from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts.models import Contact
from crm.contacts.schemas import ContactCreate


async def create_contact(session: AsyncSession, data: ContactCreate) -> Contact:
    contact = Contact(**data.model_dump())
    session.add(contact)
    await session.commit()
    await session.refresh(contact)
    return contact
