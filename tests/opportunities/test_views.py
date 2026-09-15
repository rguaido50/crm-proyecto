from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts import service as contacts_service
from crm.contacts.schemas import ContactCreate
from crm.opportunities import service
from crm.opportunities.models import OpportunityStage
from crm.opportunities.schemas import OpportunityCreate


async def test_pipeline_page_shows_a_stage_label_even_when_empty(client: AsyncClient) -> None:
    response = await client.get("/pipeline")

    assert response.status_code == 200
    assert "poc" in response.text.lower()


async def test_edit_page_shows_the_opportunitys_current_stage_selected(
    client: AsyncClient, session: AsyncSession
) -> None:
    contact = await contacts_service.create_contact(session, ContactCreate(name="Ada Lovelace"))
    opportunity = await service.create_opportunity(
        session,
        OpportunityCreate(
            contact_id=contact.id,
            title="Deal",
            owner="Sam",
            stage=OpportunityStage.PROPOSAL,
        ),
    )

    response = await client.get(f"/opportunities/{opportunity.id}/edit")

    assert response.status_code == 200
    assert 'value="proposal" selected' in response.text


async def test_create_opportunity_form_redirects_to_the_contact_detail_page(
    client: AsyncClient, session: AsyncSession
) -> None:
    contact = await contacts_service.create_contact(session, ContactCreate(name="Ada Lovelace"))

    response = await client.post(
        "/opportunities",
        data={"contact_id": contact.id, "title": "Deal", "owner": "Sam"},
    )

    assert response.status_code == 303
    assert response.headers["location"] == f"/contacts/{contact.id}"
    opportunities = await service.list_for_contact(session, contact.id)
    assert len(opportunities) == 1


async def test_update_opportunity_form_redirects_to_the_contact_detail_page(
    client: AsyncClient, session: AsyncSession
) -> None:
    contact = await contacts_service.create_contact(session, ContactCreate(name="Ada Lovelace"))
    opportunity = await service.create_opportunity(
        session, OpportunityCreate(contact_id=contact.id, title="Deal", owner="Sam")
    )

    response = await client.post(
        f"/opportunities/{opportunity.id}/edit",
        data={
            "title": "Updated deal",
            "stage": "qualified",
            "status": "open",
            "owner": "Sam",
        },
    )

    assert response.status_code == 303
    assert response.headers["location"] == f"/contacts/{contact.id}"
    updated = await service.get_opportunity(session, opportunity.id)
    assert updated.title == "Updated deal"
    assert updated.stage == OpportunityStage.QUALIFIED
