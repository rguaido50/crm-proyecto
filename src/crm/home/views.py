from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from crm.core.db import get_session
from crm.core.templates import templates
from crm.reports import service as reports_service
from crm.tasks import service as tasks_service

router = APIRouter(tags=["home-views"])


@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request, session: AsyncSession = Depends(get_session)) -> HTMLResponse:
    pipeline = await reports_service.pipeline_by_stage(session)
    open_total = sum((stage.total for stage in pipeline.values()), Decimal(0))
    open_count = sum(stage.count for stage in pipeline.values())
    funnel = await reports_service.conversion_funnel(session)
    tasks = await tasks_service.list_tasks(session)
    upcoming_tasks = [task for task in tasks if task.completed_at is None][:5]
    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "open_total": open_total,
            "open_count": open_count,
            "win_rate": funnel.win_rate,
            "upcoming_tasks": upcoming_tasks,
        },
    )
