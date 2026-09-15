from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from crm.core.db import get_session
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
    value_usd: str | None = Form(None),
    owner: str = Form(...),
    expected_close_date: str | None = Form(None),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    await service.create_opportunity(
        session,
        OpportunityCreate(
            contact_id=contact_id,
            title=title,
            value_usd=value_usd or None,
            owner=owner,
            expected_close_date=expected_close_date or None,
        ),
    )
    return RedirectResponse(url=f"/contacts/{contact_id}", status_code=303)


@router.post("/opportunities/{opportunity_id}/edit", response_class=RedirectResponse)
async def update_opportunity_form(
    opportunity_id: int,
    title: str = Form(...),
    value_usd: str | None = Form(None),
    stage: OpportunityStage = Form(...),
    status: OpportunityStatus = Form(...),
    owner: str = Form(...),
    expected_close_date: str | None = Form(None),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    opportunity = await service.update_opportunity(
        session,
        opportunity_id,
        OpportunityUpdate(
            title=title,
            value_usd=value_usd or None,
            stage=stage,
            status=status,
            owner=owner,
            expected_close_date=expected_close_date or None,
        ),
    )
    return RedirectResponse(url=f"/contacts/{opportunity.contact_id}", status_code=303)
