from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts import service
from crm.contacts.schemas import ContactCreate
from crm.opportunities import service as opportunities_service
from crm.opportunities.schemas import OpportunityCreate


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


async def test_contacts_list_page_shows_the_open_opportunity_count(
    client: AsyncClient, session: AsyncSession
) -> None:
    contact = await service.create_contact(session, ContactCreate(name="Ada Lovelace"))
    await opportunities_service.create_opportunity(
        session, OpportunityCreate(contact_id=contact.id, title="Deal", owner="Sam")
    )

    response = await client.get("/contacts")

    assert response.status_code == 200
    assert ">1<" in response.text


async def test_contact_detail_page_shows_its_opportunities_table(
    client: AsyncClient, session: AsyncSession
) -> None:
    contact = await service.create_contact(session, ContactCreate(name="Ada Lovelace"))
    await opportunities_service.create_opportunity(
        session, OpportunityCreate(contact_id=contact.id, title="itela support deal", owner="Sam")
    )

    response = await client.get(f"/contacts/{contact.id}")

    assert response.status_code == 200
    assert "itela support deal" in response.text


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


async def test_create_contact_form_with_a_blank_name_shows_an_error_on_the_contacts_page(
    client: AsyncClient,
) -> None:
    create_response = await client.post("/contacts", data={"name": "   "})

    assert create_response.headers["location"].startswith("/contacts?error=")
    response = await client.get(create_response.headers["location"])

    assert response.status_code == 200
    assert "cannot be empty" in response.text


async def test_update_contact_form_with_a_blank_name_shows_an_error_on_the_contact_page(
    client: AsyncClient, session: AsyncSession
) -> None:
    contact = await service.create_contact(session, ContactCreate(name="Ada Lovelace"))

    update_response = await client.post(f"/contacts/{contact.id}/edit", data={"name": "   "})

    assert update_response.headers["location"].startswith(f"/contacts/{contact.id}?error=")
    response = await client.get(update_response.headers["location"])

    assert response.status_code == 200
    assert "cannot be empty" in response.text


async def test_delete_contact_form_with_dependents_shows_an_error_on_the_contact_page(
    client: AsyncClient, session: AsyncSession
) -> None:
    contact = await service.create_contact(session, ContactCreate(name="Ada Lovelace"))
    contact_id = contact.id
    await opportunities_service.create_opportunity(
        session, OpportunityCreate(contact_id=contact_id, title="Deal", owner="Sam")
    )

    delete_response = await client.post(f"/contacts/{contact_id}/delete")

    assert delete_response.headers["location"].startswith(f"/contacts/{contact_id}?error=")
    response = await client.get(delete_response.headers["location"])

    assert response.status_code == 200
    assert "dependent" in response.text
    assert await service.get_contact(session, contact_id) is not None
