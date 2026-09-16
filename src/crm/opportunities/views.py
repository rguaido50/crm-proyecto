from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from crm.core.db import get_session
from crm.core.errors import ValidationError
from crm.core.redirects import contact_redirect
from crm.core.templates import templates
from crm.opportunities import service
from crm.opportunities.models import OpportunityStage, OpportunityStatus
from crm.opportunities.schemas import OpportunityCreate, OpportunityUpdate

router = APIRouter(tags=["opportunities-views"])


@router.get("/pipeline", response_class=HTMLResponse)
async def pipeline_page(
    request: Request, session: AsyncSession = Depends(get_session)
) -> HTMLResponse:
    board = await service.list_open_by_stage(session)
    return templates.TemplateResponse(request, "pipeline.html", {"board": board})


@router.get("/opportunities/{opportunity_id}/edit", response_class=HTMLResponse)
async def edit_opportunity_page(
    opportunity_id: int, request: Request, session: AsyncSession = Depends(get_session)
) -> HTMLResponse:
    opportunity = await service.get_opportunity(session, opportunity_id)
    return templates.TemplateResponse(
        request,
        "edit.html",
        {
            "opportunity": opportunity,
            "stages": list(OpportunityStage),
            "statuses": list(OpportunityStatus),
        },
    )


@router.post("/opportunities", response_class=RedirectResponse)
async def create_opportunity_form(
    contact_id: int = Form(...),
    title: str = Form(...),
    value_usd: Decimal | None = Form(None),
    owner: str = Form(...),
    expected_close_date: date | None = Form(None),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    error = None
    try:
        await service.create_opportunity(
            session,
            OpportunityCreate(
                contact_id=contact_id,
                title=title,
                value_usd=value_usd,
                owner=owner,
                expected_close_date=expected_close_date,
            ),
        )
    except ValidationError as exc:
        error = str(exc)
    return contact_redirect(contact_id, error)


@router.post("/opportunities/{opportunity_id}/edit", response_class=RedirectResponse)
async def update_opportunity_form(
    opportunity_id: int,
    title: str = Form(...),
    value_usd: Decimal | None = Form(None),
    stage: OpportunityStage = Form(...),
    status: OpportunityStatus = Form(...),
    owner: str = Form(...),
    expected_close_date: date | None = Form(None),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    contact_id = (await service.get_opportunity(session, opportunity_id)).contact_id
    error = None
    try:
        await service.update_opportunity(
            session,
            opportunity_id,
            OpportunityUpdate(
                title=title,
                value_usd=value_usd,
                stage=stage,
                status=status,
                owner=owner,
                expected_close_date=expected_close_date,
            ),
        )
    except ValidationError as exc:
        error = str(exc)
    return contact_redirect(contact_id, error)
