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
