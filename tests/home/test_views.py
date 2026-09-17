from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts import service as contacts_service
from crm.contacts.schemas import ContactCreate
from crm.opportunities import service as opportunities_service
from crm.opportunities.schemas import OpportunityCreate
from crm.tasks import service as tasks_service
from crm.tasks.models import TaskType
from crm.tasks.schemas import TaskCreate


async def test_home_page_shows_the_open_pipeline_total(
    client: AsyncClient, session: AsyncSession
) -> None:
    contact = await contacts_service.create_contact(session, ContactCreate(name="Ada Lovelace"))
    await opportunities_service.create_opportunity(
        session,
        OpportunityCreate(
            contact_id=contact.id, title="Deal", owner="Sam", value_usd=Decimal(1000)
        ),
    )

    response = await client.get("/")

    assert response.status_code == 200
    assert "$1000.00" in response.text


async def test_home_page_shows_a_placeholder_win_rate_when_there_is_no_closed_data(
    client: AsyncClient,
) -> None:
    response = await client.get("/")

    assert response.status_code == 200
    assert "—" in response.text


async def test_home_page_shows_an_upcoming_pending_tasks_title(
    client: AsyncClient, session: AsyncSession
) -> None:
    contact = await contacts_service.create_contact(session, ContactCreate(name="Ada Lovelace"))
    await tasks_service.create_task(
        session,
        TaskCreate(
            contact_id=contact.id, title="Call about renewal", type=TaskType.CALL, owner="Sam"
        ),
    )

    response = await client.get("/")

    assert response.status_code == 200
    assert "Call about renewal" in response.text


async def test_home_page_upcoming_tasks_excludes_completed_tasks(
    client: AsyncClient, session: AsyncSession
) -> None:
    contact = await contacts_service.create_contact(session, ContactCreate(name="Ada Lovelace"))
    task = await tasks_service.create_task(
        session,
        TaskCreate(contact_id=contact.id, title="Already done", type=TaskType.CALL, owner="Sam"),
    )
    await tasks_service.complete_task(session, task.id)

    response = await client.get("/")

    assert response.status_code == 200
    assert "Already done" not in response.text
