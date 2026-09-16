from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts.models import Contact
from crm.contacts.schemas import ContactCreate, ContactUpdate
from crm.core.errors import HasDependentsError, NotFoundError, ValidationError
from crm.core.validation import require_non_blank

# Opportunity belongs to Contact (FK); this reverse import is deliberate — list_contacts
# needs the open-Opportunity count per #12's ticket, and there's no repository layer to
# put it behind (see CLAUDE.md). Contacts is otherwise a leaf module.
from crm.opportunities.models import Opportunity, OpportunityStatus


class ContactNotFoundError(NotFoundError):
    pass


class ContactHasDependentsError(HasDependentsError):
    pass


class ContactValidationError(ValidationError):
    pass


def _normalize(data: dict[str, str | None]) -> dict[str, str | None]:
    normalized: dict[str, str | None] = {}
    for field, value in data.items():
        normalized[field] = (value.strip() or None) if value is not None else None
    if "name" in normalized:
        normalized["name"] = require_non_blank(
            normalized["name"] or "", "name", ContactValidationError
        )
    return normalized


async def create_contact(session: AsyncSession, data: ContactCreate) -> Contact:
    contact = Contact(**_normalize(data.model_dump()))
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


async def list_contacts_with_open_counts(session: AsyncSession) -> list[tuple[Contact, int]]:
    open_opportunities_count = (
        select(func.count(Opportunity.id))
        .where(
            Opportunity.contact_id == Contact.id,
            Opportunity.status == OpportunityStatus.OPEN,
        )
        .correlate(Contact)
        .scalar_subquery()
    )
    result = await session.execute(select(Contact, open_opportunities_count).order_by(Contact.name))
    return list(result.tuples().all())


async def update_contact(session: AsyncSession, contact_id: int, data: ContactUpdate) -> Contact:
    contact = await get_contact(session, contact_id)
    updates = _normalize(data.model_dump(exclude_unset=True))
    for field, value in updates.items():
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
