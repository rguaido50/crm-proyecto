from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts import service
from crm.contacts.schemas import ContactCreate, ContactUpdate
from crm.core.db import get_session
from crm.core.templates import templates
from crm.opportunities import service as opportunities_service

router = APIRouter(tags=["contacts-views"])


@router.get("/contacts", response_class=HTMLResponse)
async def list_contacts_page(
    request: Request, session: AsyncSession = Depends(get_session)
) -> HTMLResponse:
    contacts = await service.list_contacts(session)
    return templates.TemplateResponse(request, "list.html", {"contacts": contacts})


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
    name: str = Form(...),
    company: str | None = Form(None),
    email: str | None = Form(None),
    phone: str | None = Form(None),
    notes: str | None = Form(None),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    await service.create_contact(
        session,
        ContactCreate(name=name, company=company, email=email, phone=phone, notes=notes),
    )
    return RedirectResponse(url="/contacts", status_code=303)


@router.post("/contacts/{contact_id}/edit", response_class=RedirectResponse)
async def update_contact_form(
    contact_id: int,
    name: str = Form(...),
    company: str | None = Form(None),
    email: str | None = Form(None),
    phone: str | None = Form(None),
    notes: str | None = Form(None),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    await service.update_contact(
        session,
        contact_id,
        ContactUpdate(name=name, company=company, email=email, phone=phone, notes=notes),
    )
    return RedirectResponse(url=f"/contacts/{contact_id}", status_code=303)


@router.post("/contacts/{contact_id}/delete", response_class=RedirectResponse)
async def delete_contact_form(
    contact_id: int, session: AsyncSession = Depends(get_session)
) -> RedirectResponse:
    await service.delete_contact(session, contact_id)
    return RedirectResponse(url="/contacts", status_code=303)
