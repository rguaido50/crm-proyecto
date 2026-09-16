from datetime import date
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from crm.core.db import get_session
from crm.core.errors import ValidationError
from crm.core.templates import templates
from crm.tasks import service
from crm.tasks.models import TaskType
from crm.tasks.schemas import TaskCreate

router = APIRouter(tags=["tasks-views"])


def _contact_redirect(contact_id: int, error: str | None) -> RedirectResponse:
    url = f"/contacts/{contact_id}"
    if error:
        url += f"?error={quote(error)}"
    return RedirectResponse(url=url, status_code=303)


@router.get("/tasks", response_class=HTMLResponse)
async def list_tasks_page(
    request: Request, session: AsyncSession = Depends(get_session)
) -> HTMLResponse:
    tasks = await service.list_tasks(session)
    return templates.TemplateResponse(request, "list.html", {"tasks": tasks})


@router.post("/tasks", response_class=RedirectResponse)
async def create_task_form(
    contact_id: int = Form(...),
    opportunity_id: int | None = Form(None),
    title: str = Form(...),
    description: str | None = Form(None),
    type: TaskType = Form(...),
    due_date: date | None = Form(None),
    owner: str = Form(...),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    error = None
    try:
        await service.create_task(
            session,
            TaskCreate(
                contact_id=contact_id,
                opportunity_id=opportunity_id,
                title=title,
                description=description,
                type=type,
                due_date=due_date,
                owner=owner,
            ),
        )
    except ValidationError as exc:
        error = str(exc)
    return _contact_redirect(contact_id, error)


@router.post("/tasks/{task_id}/complete", response_class=RedirectResponse)
async def complete_task_form(
    task_id: int, request: Request, session: AsyncSession = Depends(get_session)
) -> RedirectResponse:
    await service.complete_task(session, task_id)
    return RedirectResponse(url=request.headers.get("referer", "/tasks"), status_code=303)
