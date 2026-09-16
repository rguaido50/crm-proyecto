from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts import service as contacts_service
from crm.contacts.schemas import ContactCreate
from crm.opportunities import service as opportunities_service
from crm.opportunities.schemas import OpportunityCreate
from crm.tasks import service
from crm.tasks.models import TaskType
from crm.tasks.schemas import TaskCreate


async def test_tasks_list_page_shows_a_seeded_pending_tasks_title(
    client: AsyncClient, session: AsyncSession
) -> None:
    contact = await contacts_service.create_contact(session, ContactCreate(name="Ada Lovelace"))
    await service.create_task(
        session,
        TaskCreate(
            contact_id=contact.id, title="Call about renewal", type=TaskType.CALL, owner="Sam"
        ),
    )

    response = await client.get("/tasks")

    assert response.status_code == 200
    assert "Call about renewal" in response.text


async def test_create_task_form_redirects_to_the_contact_detail_page(
    client: AsyncClient, session: AsyncSession
) -> None:
    contact = await contacts_service.create_contact(session, ContactCreate(name="Ada Lovelace"))

    response = await client.post(
        "/tasks",
        data={
            "contact_id": contact.id,
            "title": "Call about renewal",
            "type": "call",
            "owner": "Sam",
        },
    )

    assert response.status_code == 303
    assert response.headers["location"] == f"/contacts/{contact.id}"
    tasks = await service.list_pending_for_contact(session, contact.id)
    assert len(tasks) == 1


async def test_create_task_form_from_an_opportunity_derives_the_contact(
    client: AsyncClient, session: AsyncSession
) -> None:
    real_contact = await contacts_service.create_contact(
        session, ContactCreate(name="Ada Lovelace")
    )
    other_contact = await contacts_service.create_contact(
        session, ContactCreate(name="Grace Hopper")
    )
    opportunity = await opportunities_service.create_opportunity(
        session, OpportunityCreate(contact_id=real_contact.id, title="Deal", owner="Sam")
    )

    response = await client.post(
        "/tasks",
        data={
            "contact_id": other_contact.id,
            "opportunity_id": opportunity.id,
            "title": "Deal follow-up",
            "type": "email",
            "owner": "Sam",
        },
    )

    assert response.status_code == 303
    assert response.headers["location"] == f"/contacts/{real_contact.id}"
    real_contact_tasks = await service.list_pending_for_contact(session, real_contact.id)
    assert len(real_contact_tasks) == 1


async def test_create_task_form_with_an_invalid_opportunity_id_redirects_with_an_error(
    client: AsyncClient, session: AsyncSession
) -> None:
    contact = await contacts_service.create_contact(session, ContactCreate(name="Ada Lovelace"))

    response = await client.post(
        "/tasks",
        data={
            "contact_id": contact.id,
            "opportunity_id": 999999,
            "title": "Deal follow-up",
            "type": "email",
            "owner": "Sam",
        },
    )

    assert response.status_code == 303
    assert response.headers["location"].startswith(f"/contacts/{contact.id}?error=")
    assert await service.list_pending_for_contact(session, contact.id) == []


async def test_create_task_form_with_a_blank_title_redirects_to_the_contact_with_an_error(
    client: AsyncClient, session: AsyncSession
) -> None:
    contact = await contacts_service.create_contact(session, ContactCreate(name="Ada Lovelace"))

    response = await client.post(
        "/tasks", data={"contact_id": contact.id, "title": "   ", "type": "call", "owner": "Sam"}
    )

    assert response.status_code == 303
    assert response.headers["location"].startswith(f"/contacts/{contact.id}?error=")
    assert await service.list_pending_for_contact(session, contact.id) == []


async def test_complete_task_form_redirects_to_the_contact_detail_page(
    client: AsyncClient, session: AsyncSession
) -> None:
    contact = await contacts_service.create_contact(session, ContactCreate(name="Ada Lovelace"))
    task = await service.create_task(
        session,
        TaskCreate(contact_id=contact.id, title="Call back", type=TaskType.CALL, owner="Sam"),
    )

    response = await client.post(
        f"/tasks/{task.id}/complete", headers={"referer": "https://evil.example/phish"}
    )

    assert response.status_code == 303
    assert response.headers["location"] == f"/contacts/{contact.id}"
    completed = await service.get_task(session, task.id)
    assert completed.completed_at is not None
