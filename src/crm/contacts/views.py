from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts import service
from crm.contacts.schemas import ContactCreate, ContactUpdate
from crm.core.db import get_session
from crm.core.errors import HAS_DEPENDENTS_MESSAGE, HasDependentsError, ValidationError
from crm.core.responses import redirect_with_error
from crm.core.templates import templates
from crm.opportunities import service as opportunities_service

router = APIRouter(tags=["contacts-views"])


@router.get("/contacts", response_class=HTMLResponse)
async def list_contacts_page(
    request: Request, error: str | None = None, session: AsyncSession = Depends(get_session)
) -> HTMLResponse:
    contacts = await service.list_contacts_with_open_counts(session)
    return templates.TemplateResponse(request, "list.html", {"contacts": contacts, "error": error})


@router.get("/contacts/{contact_id}", response_class=HTMLResponse)
async def contact_detail_page(
    contact_id: int,
    request: Request,
    error: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    contact = await service.get_contact(session, contact_id)
    opportunities = await opportunities_service.list_for_contact(session, contact_id)
    return templates.TemplateResponse(
        request,
        "detail.html",
        {"contact": contact, "opportunities": opportunities, "error": error},
    )


@router.post("/contacts", response_class=RedirectResponse)
async def create_contact_form(
    data: Annotated[ContactCreate, Form()],
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    error = None
    try:
        await service.create_contact(session, data)
    except ValidationError as exc:
        error = str(exc)
    return redirect_with_error("/contacts", error)


@router.post("/contacts/{contact_id}/edit", response_class=RedirectResponse)
async def update_contact_form(
    contact_id: int,
    data: Annotated[ContactUpdate, Form()],
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    error = None
    try:
        await service.update_contact(session, contact_id, data)
    except ValidationError as exc:
        error = str(exc)
    return redirect_with_error(f"/contacts/{contact_id}", error)


@router.post("/contacts/{contact_id}/delete", response_class=RedirectResponse)
async def delete_contact_form(
    contact_id: int, session: AsyncSession = Depends(get_session)
) -> RedirectResponse:
    error = None
    try:
        await service.delete_contact(session, contact_id)
    except HasDependentsError:
        error = HAS_DEPENDENTS_MESSAGE
    if error:
        return redirect_with_error(f"/contacts/{contact_id}", error)
    return RedirectResponse(url="/contacts", status_code=303)
