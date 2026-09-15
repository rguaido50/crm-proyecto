from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts import service
from crm.contacts.models import Contact
from crm.contacts.schemas import ContactCreate, ContactRead, ContactUpdate
from crm.core.db import get_session

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.post("", response_model=ContactRead, status_code=201)
async def create_contact(
    data: ContactCreate, session: AsyncSession = Depends(get_session)
) -> Contact:
    return await service.create_contact(session, data)


@router.get("", response_model=list[ContactRead])
async def list_contacts(
    session: AsyncSession = Depends(get_session),
) -> list[Contact]:
    return await service.list_contacts(session)


@router.get("/{contact_id}", response_model=ContactRead)
async def get_contact(contact_id: int, session: AsyncSession = Depends(get_session)) -> Contact:
    return await service.get_contact(session, contact_id)


@router.patch("/{contact_id}", response_model=ContactRead)
async def update_contact(
    contact_id: int, data: ContactUpdate, session: AsyncSession = Depends(get_session)
) -> Contact:
    return await service.update_contact(session, contact_id, data)


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(contact_id: int, session: AsyncSession = Depends(get_session)) -> None:
    await service.delete_contact(session, contact_id)
