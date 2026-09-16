from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from crm.core.db import get_session
from crm.tasks import service
from crm.tasks.models import Task
from crm.tasks.schemas import TaskCreate, TaskRead

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead, status_code=201)
async def create_task(data: TaskCreate, session: AsyncSession = Depends(get_session)) -> Task:
    return await service.create_task(session, data)


@router.get("", response_model=list[TaskRead])
async def list_tasks(session: AsyncSession = Depends(get_session)) -> list[Task]:
    return await service.list_tasks(session)


@router.patch("/{task_id}", response_model=TaskRead)
async def complete_task(task_id: int, session: AsyncSession = Depends(get_session)) -> Task:
    return await service.complete_task(session, task_id)
