from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts import service
from crm.contacts.schemas import ContactCreate


async def test_contacts_list_page_shows_a_seeded_contact(
    client: AsyncClient, session: AsyncSession
) -> None:
    await service.create_contact(session, ContactCreate(name="Ada Lovelace"))

    response = await client.get("/contacts")

    assert response.status_code == 200
    assert "Ada Lovelace" in response.text


async def test_contact_detail_page_shows_the_activity_history_section(
    client: AsyncClient, session: AsyncSession
) -> None:
    contact = await service.create_contact(session, ContactCreate(name="Ada Lovelace"))

    response = await client.get(f"/contacts/{contact.id}")

    assert response.status_code == 200
    assert "Activity history" in response.text


async def test_detail_page_redirects_instead_of_500ing_for_a_missing_contact(
    client: AsyncClient,
) -> None:
    response = await client.get("/contacts/999999")

    assert response.status_code == 303


async def test_create_contact_form_stores_a_blank_optional_field_as_null(
    client: AsyncClient, session: AsyncSession
) -> None:
    response = await client.post("/contacts", data={"name": "Ada Lovelace", "company": ""})

    assert response.status_code == 303
    contacts = await service.list_contacts(session)
    assert contacts[0].company is None


async def test_create_contact_form_redirects_instead_of_500ing_for_a_whitespace_name(
    client: AsyncClient, session: AsyncSession
) -> None:
    response = await client.post("/contacts", data={"name": "   "})

    assert response.status_code == 303
    assert await service.list_contacts(session) == []
