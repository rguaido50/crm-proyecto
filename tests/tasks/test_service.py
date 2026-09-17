from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts import service as contacts_service
from crm.contacts.models import Contact
from crm.contacts.schemas import ContactCreate
from crm.opportunities import service as opportunities_service
from crm.opportunities.models import Opportunity
from crm.opportunities.schemas import OpportunityCreate
from crm.tasks import service
from crm.tasks.models import TaskType
from crm.tasks.schemas import TaskCreate


async def _make_contact(session: AsyncSession, name: str = "Ada Lovelace") -> Contact:
    return await contacts_service.create_contact(session, ContactCreate(name=name))


async def _make_opportunity(session: AsyncSession, contact: Contact) -> Opportunity:
    return await opportunities_service.create_opportunity(
        session, OpportunityCreate(contact_id=contact.id, title="Deal", owner="Sam")
    )


async def test_create_task_persists_the_given_fields(session: AsyncSession) -> None:
    contact = await _make_contact(session)

    task = await service.create_task(
        session,
        TaskCreate(contact_id=contact.id, title="Follow up call", type=TaskType.CALL, owner="Sam"),
    )

    assert task.id is not None
    assert task.contact_id == contact.id
    assert task.title == "Follow up call"
    assert task.type == TaskType.CALL
    assert task.completed_at is None


async def test_create_task_stores_a_blank_description_as_null(session: AsyncSession) -> None:
    contact = await _make_contact(session)

    task = await service.create_task(
        session,
        TaskCreate(
            contact_id=contact.id,
            title="Follow up call",
            type=TaskType.CALL,
            owner="Sam",
            description="   ",
        ),
    )

    assert task.description is None


async def test_create_task_rejects_an_invalid_contact_id(session: AsyncSession) -> None:
    with pytest.raises(service.TaskValidationError, match="^invalid task data$"):
        await service.create_task(
            session,
            TaskCreate(contact_id=999999, title="Ghost task", type=TaskType.CALL, owner="Sam"),
        )


async def test_create_task_rejects_a_blank_title(session: AsyncSession) -> None:
    contact = await _make_contact(session)

    with pytest.raises(service.TaskValidationError, match="^title cannot be empty$"):
        await service.create_task(
            session, TaskCreate(contact_id=contact.id, title="   ", type=TaskType.CALL, owner="Sam")
        )


async def test_create_task_rejects_a_blank_owner(session: AsyncSession) -> None:
    contact = await _make_contact(session)

    with pytest.raises(service.TaskValidationError, match="^owner cannot be empty$"):
        await service.create_task(
            session, TaskCreate(contact_id=contact.id, title="Follow up", type=TaskType.CALL, owner="  ")
        )


async def test_create_task_trims_a_non_blank_description(session: AsyncSession) -> None:
    contact = await _make_contact(session)

    task = await service.create_task(
        session,
        TaskCreate(
            contact_id=contact.id,
            title="Follow up call",
            type=TaskType.CALL,
            owner="Sam",
            description="  Client requested a callback  ",
        ),
    )

    assert task.description == "Client requested a callback"


async def test_create_task_rejects_an_invalid_opportunity_id(session: AsyncSession) -> None:
    contact = await _make_contact(session)

    with pytest.raises(service.TaskValidationError, match="^opportunity not found$"):
        await service.create_task(
            session,
            TaskCreate(
                contact_id=contact.id,
                opportunity_id=999999,
                title="Deal follow-up",
                type=TaskType.EMAIL,
                owner="Sam",
            ),
        )


async def test_create_task_from_an_opportunity_overrides_a_mismatched_contact_id(
    session: AsyncSession,
) -> None:
    real_contact = await _make_contact(session, "Ada Lovelace")
    other_contact = await _make_contact(session, "Grace Hopper")
    opportunity = await _make_opportunity(session, real_contact)

    task = await service.create_task(
        session,
        TaskCreate(
            contact_id=other_contact.id,
            opportunity_id=opportunity.id,
            title="Deal follow-up",
            type=TaskType.EMAIL,
            owner="Sam",
        ),
    )

    assert task.contact_id == real_contact.id


async def test_get_task_raises_for_a_missing_id(session: AsyncSession) -> None:
    with pytest.raises(service.TaskNotFoundError, match="^999999$"):
        await service.get_task(session, 999999)


async def test_list_tasks_orders_pending_first_with_nulls_last_due_dates(
    session: AsyncSession,
) -> None:
    contact = await _make_contact(session)
    undated = await service.create_task(
        session,
        TaskCreate(contact_id=contact.id, title="Undated", type=TaskType.OTHER, owner="Sam"),
    )
    due_later = await service.create_task(
        session,
        TaskCreate(
            contact_id=contact.id,
            title="Due later",
            type=TaskType.OTHER,
            owner="Sam",
            due_date=date(2026, 12, 1),
        ),
    )
    due_sooner = await service.create_task(
        session,
        TaskCreate(
            contact_id=contact.id,
            title="Due sooner",
            type=TaskType.OTHER,
            owner="Sam",
            due_date=date(2026, 10, 1),
        ),
    )
    completed = await service.create_task(
        session,
        TaskCreate(
            contact_id=contact.id,
            title="Already done",
            type=TaskType.OTHER,
            owner="Sam",
            due_date=date(2026, 1, 1),
        ),
    )
    await service.complete_task(session, completed.id)

    tasks = await service.list_tasks(session)

    assert [task.id for task in tasks] == [due_sooner.id, due_later.id, undated.id, completed.id]


async def test_list_pending_for_contact_excludes_completed_tasks(session: AsyncSession) -> None:
    contact = await _make_contact(session)
    pending = await service.create_task(
        session, TaskCreate(contact_id=contact.id, title="Pending", type=TaskType.CALL, owner="Sam")
    )
    done = await service.create_task(
        session, TaskCreate(contact_id=contact.id, title="Done", type=TaskType.CALL, owner="Sam")
    )
    await service.complete_task(session, done.id)

    pending_tasks = await service.list_pending_for_contact(session, contact.id)

    assert [task.id for task in pending_tasks] == [pending.id]


async def test_list_activity_for_contact_returns_completed_tasks_most_recent_first(
    session: AsyncSession,
) -> None:
    contact = await _make_contact(session)
    other_contact = await _make_contact(session, "Grace Hopper")
    pending = await service.create_task(
        session, TaskCreate(contact_id=contact.id, title="Pending", type=TaskType.CALL, owner="Sam")
    )
    first_done = await service.create_task(
        session, TaskCreate(contact_id=contact.id, title="First", type=TaskType.CALL, owner="Sam")
    )
    second_done = await service.create_task(
        session, TaskCreate(contact_id=contact.id, title="Second", type=TaskType.CALL, owner="Sam")
    )
    other_done = await service.create_task(
        session,
        TaskCreate(contact_id=other_contact.id, title="Other", type=TaskType.CALL, owner="Sam"),
    )
    await service.complete_task(session, first_done.id)
    await service.complete_task(session, second_done.id)
    await service.complete_task(session, other_done.id)

    activity = await service.list_activity_for_contact(session, contact.id)

    assert [task.id for task in activity] == [second_done.id, first_done.id]
    assert pending.id not in [task.id for task in activity]


async def test_complete_task_sets_completed_at(session: AsyncSession) -> None:
    contact = await _make_contact(session)
    task = await service.create_task(
        session,
        TaskCreate(contact_id=contact.id, title="Call back", type=TaskType.CALL, owner="Sam"),
    )
    assert task.completed_at is None

    completed = await service.complete_task(session, task.id)

    assert completed.completed_at is not None
    assert completed.completed_at.tzinfo is not None
