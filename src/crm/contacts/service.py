from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts.models import Contact
from crm.contacts.schemas import ContactCreate, ContactUpdate
from crm.core.errors import HasDependentsError, NotFoundError


class ContactNotFoundError(NotFoundError):
    pass


class ContactHasDependentsError(HasDependentsError):
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


async def list_contacts(session: AsyncSession) -> list[Contact]:
    result = await session.execute(select(Contact).order_by(Contact.name))
    return list(result.scalars().all())


async def update_contact(session: AsyncSession, contact_id: int, data: ContactUpdate) -> Contact:
    contact = await get_contact(session, contact_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    await session.commit()
    await session.refresh(contact)
    return contact


async def delete_contact(session: AsyncSession, contact_id: int) -> None:
    contact = await get_contact(session, contact_id)
    await session.delete(contact)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ContactHasDependentsError(contact_id) from exc
