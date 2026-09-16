import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from crm.contacts.models import Contact
from crm.core.db import Base


class TaskType(str, enum.Enum):
    CALL = "call"
    MEETING = "meeting"
    EMAIL = "email"
    OTHER = "other"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int] = mapped_column(
        ForeignKey("contacts.id", ondelete="RESTRICT"), index=True
    )
    opportunity_id: Mapped[int | None] = mapped_column(
        ForeignKey("opportunities.id", ondelete="RESTRICT"), index=True
    )
    title: Mapped[str]
    description: Mapped[str | None] = mapped_column(Text)
    type: Mapped[TaskType] = mapped_column(
        Enum(TaskType, values_callable=lambda cls: [e.value for e in cls])
    )
    due_date: Mapped[date | None] = mapped_column(Date)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    owner: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    contact: Mapped[Contact] = relationship()
