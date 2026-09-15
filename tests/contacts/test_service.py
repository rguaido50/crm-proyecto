import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts import service
from crm.contacts.schemas import ContactCreate, ContactUpdate


async def test_create_contact_persists_the_given_fields(session: AsyncSession) -> None:
    contact = await service.create_contact(
        session,
        ContactCreate(name="Ada Lovelace", company="Acme", email="ada@acme.com"),
    )

    assert contact.id is not None
    assert contact.name == "Ada Lovelace"
    assert contact.company == "Acme"
    assert contact.email == "ada@acme.com"


async def test_get_contact_returns_the_matching_contact(session: AsyncSession) -> None:
    created = await service.create_contact(session, ContactCreate(name="Grace Hopper"))

    fetched = await service.get_contact(session, created.id)

    assert fetched.id == created.id
    assert fetched.name == "Grace Hopper"


async def test_get_contact_raises_for_a_missing_id(session: AsyncSession) -> None:
    with pytest.raises(service.ContactNotFoundError):
        await service.get_contact(session, 999999)


async def test_list_contacts_returns_every_contact(session: AsyncSession) -> None:
    await service.create_contact(session, ContactCreate(name="Ada Lovelace"))
    await service.create_contact(session, ContactCreate(name="Grace Hopper"))

    contacts = await service.list_contacts(session)

    names = {contact.name for contact in contacts}
    assert names == {"Ada Lovelace", "Grace Hopper"}


async def test_update_contact_changes_only_the_given_fields(session: AsyncSession) -> None:
    created = await service.create_contact(
        session, ContactCreate(name="Ada Lovelace", company="Acme")
    )

    updated = await service.update_contact(
        session, created.id, ContactUpdate(company="New Co")
    )

    assert updated.name == "Ada Lovelace"
    assert updated.company == "New Co"
