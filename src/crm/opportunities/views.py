from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from crm.core.db import get_session
from crm.core.errors import NotFoundError, ValidationError
from crm.core.responses import redirect_with_error
from crm.core.templates import templates
from crm.opportunities import service
from crm.opportunities.models import OpportunityStage, OpportunityStatus
from crm.opportunities.schemas import OpportunityCreate, OpportunityUpdate

router = APIRouter(tags=["opportunities-views"])


@router.get("/pipeline", response_class=HTMLResponse)
async def pipeline_page(
    request: Request, error: str | None = None, session: AsyncSession = Depends(get_session)
) -> HTMLResponse:
    board = await service.list_open_by_stage(session)
    return templates.TemplateResponse(request, "pipeline.html", {"board": board, "error": error})


@router.get(
    "/opportunities/{opportunity_id}/edit", response_class=HTMLResponse, response_model=None
)
async def edit_opportunity_page(
    opportunity_id: int, request: Request, session: AsyncSession = Depends(get_session)
) -> Response:
    try:
        opportunity = await service.get_opportunity(session, opportunity_id)
    except NotFoundError:
        return redirect_with_error("/pipeline", "Opportunity not found")
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
    data: Annotated[OpportunityCreate, Form()],
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    error = None
    try:
        await service.create_opportunity(session, data)
    except ValidationError as exc:
        error = str(exc)
    return redirect_with_error(f"/contacts/{data.contact_id}", error)


@router.post("/opportunities/{opportunity_id}/edit", response_class=RedirectResponse)
async def update_opportunity_form(
    opportunity_id: int,
    data: Annotated[OpportunityUpdate, Form()],
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    try:
        contact_id = (await service.get_opportunity(session, opportunity_id)).contact_id
    except NotFoundError:
        return redirect_with_error("/pipeline", "Opportunity not found")
    error = None
    try:
        await service.update_opportunity(session, opportunity_id, data)
    except ValidationError as exc:
        error = str(exc)
    return redirect_with_error(f"/contacts/{contact_id}", error)
