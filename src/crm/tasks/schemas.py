from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from crm.tasks.models import TaskType


class TaskCreate(BaseModel):
    contact_id: int
    opportunity_id: int | None = None
    title: str = Field(max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    type: TaskType
    due_date: date | None = None
    owner: str = Field(max_length=100)


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contact_id: int
    opportunity_id: int | None
    title: str
    description: str | None
    type: TaskType
    due_date: date | None
    completed_at: datetime | None
    owner: str
    created_at: datetime
    updated_at: datetime
