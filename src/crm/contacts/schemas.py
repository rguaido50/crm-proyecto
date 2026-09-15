from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ContactCreate(BaseModel):
    name: str
    company: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str | None = None


class ContactUpdate(ContactCreate):
    name: str | None = None  # type: ignore[assignment]


class ContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    company: str | None
    email: str | None
    phone: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
