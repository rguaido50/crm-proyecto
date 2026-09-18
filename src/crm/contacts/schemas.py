from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ContactCreate(BaseModel):
    name: str = Field(max_length=200)
    company: str | None = Field(default=None, max_length=200)
    email: str | None = None
    phone: str | None = None
    notes: str | None = Field(default=None, max_length=2000)


class ContactUpdate(ContactCreate):
    name: str | None = Field(default=None, max_length=200)  # type: ignore[assignment]


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
