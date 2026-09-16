from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts import service
from crm.contacts.schemas import ContactCreate
from crm.opportunities import service as opportunities_service
from crm.opportunities.schemas import OpportunityCreate


async def test_create_contact_returns_201_with_the_created_row(client: AsyncClient) -> None:
    response = await client.post("/api/contacts", json={"name": "Ada Lovelace"})

    assert response.status_code == 201
    assert response.json()["name"] == "Ada Lovelace"


async def test_get_contact_returns_404_for_a_missing_id(client: AsyncClient) -> None:
    response = await client.get("/api/contacts/999999")

    assert response.status_code == 404


async def test_create_contact_rejects_a_blank_name(client: AsyncClient) -> None:
    response = await client.post("/api/contacts", json={"name": ""})

    assert response.status_code == 422


async def test_update_contact_rejects_an_explicit_null_name(client: AsyncClient) -> None:
    created = await client.post("/api/contacts", json={"name": "Ada Lovelace"})

    response = await client.patch(f"/api/contacts/{created.json()['id']}", json={"name": None})

    assert response.status_code == 422


async def test_delete_contact_returns_409_when_it_has_opportunities(
    client: AsyncClient, session: AsyncSession
) -> None:
    contact = await service.create_contact(session, ContactCreate(name="Ada Lovelace"))
    contact_id = contact.id
    await opportunities_service.create_opportunity(
        session, OpportunityCreate(contact_id=contact_id, title="Deal", owner="Sam")
    )

    response = await client.delete(f"/api/contacts/{contact_id}")

    assert response.status_code == 409
    assert await service.get_contact(session, contact_id) is not None
