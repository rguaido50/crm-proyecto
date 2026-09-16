from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from crm.core.errors import NotFoundError, ValidationError
from crm.core.validation import require_non_blank
from crm.opportunities import service as opportunities_service
from crm.tasks.models import Task
from crm.tasks.schemas import TaskCreate


class TaskNotFoundError(NotFoundError):
    pass


class TaskValidationError(ValidationError):
    pass


async def create_task(session: AsyncSession, data: TaskCreate) -> Task:
    fields = data.model_dump()
    fields["title"] = require_non_blank(fields["title"], "title", TaskValidationError)
    fields["owner"] = require_non_blank(fields["owner"], "owner", TaskValidationError)
    if fields["description"] is not None:
        fields["description"] = fields["description"].strip() or None
    if fields["opportunity_id"] is not None:
        opportunity = await opportunities_service.get_opportunity(
            session, fields["opportunity_id"]
        )
        fields["contact_id"] = opportunity.contact_id
    task = Task(**fields)
    session.add(task)
    try:
        await session.commit()
    except DBAPIError as exc:
        await session.rollback()
        raise TaskValidationError("invalid task data") from exc
    await session.refresh(task)
    return task


async def get_task(session: AsyncSession, task_id: int) -> Task:
    task = await session.get(Task, task_id)
    if task is None:
        raise TaskNotFoundError(task_id)
    return task


async def list_tasks(session: AsyncSession) -> list[Task]:
    result = await session.execute(
        select(Task)
        .options(joinedload(Task.contact))
        .order_by(
            Task.completed_at.is_not(None),
            Task.due_date.is_(None),
            Task.due_date,
        )
    )
    return list(result.scalars().all())


async def list_pending_for_contact(session: AsyncSession, contact_id: int) -> list[Task]:
    result = await session.execute(
        select(Task)
        .where(Task.contact_id == contact_id, Task.completed_at.is_(None))
        .order_by(Task.due_date.is_(None), Task.due_date)
    )
    return list(result.scalars().all())


async def list_activity_for_contact(session: AsyncSession, contact_id: int) -> list[Task]:
    result = await session.execute(
        select(Task)
        .where(Task.contact_id == contact_id, Task.completed_at.is_not(None))
        .order_by(Task.completed_at.desc())
    )
    return list(result.scalars().all())


async def complete_task(session: AsyncSession, task_id: int) -> Task:
    task = await get_task(session, task_id)
    task.completed_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(task)
    return task
