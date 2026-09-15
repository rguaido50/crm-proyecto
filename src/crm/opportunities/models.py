import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from crm.contacts.models import Contact
from crm.core.db import Base


class OpportunityStage(str, enum.Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    POC = "poc"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"


class OpportunityStatus(str, enum.Enum):
    OPEN = "open"
    WON = "won"
    LOST = "lost"


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id", ondelete="RESTRICT"))
    title: Mapped[str]
    value_usd: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    stage: Mapped[OpportunityStage] = mapped_column(
        Enum(OpportunityStage, values_callable=lambda cls: [e.value for e in cls]),
        default=OpportunityStage.NEW,
    )
    status: Mapped[OpportunityStatus] = mapped_column(
        Enum(OpportunityStatus, values_callable=lambda cls: [e.value for e in cls]),
        default=OpportunityStatus.OPEN,
    )
    expected_close_date: Mapped[date | None] = mapped_column(Date)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    owner: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    contact: Mapped[Contact] = relationship()
