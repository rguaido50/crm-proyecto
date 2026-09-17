"""Demo seed data. Single deliberate run: `python -m crm.seed`.

Reproduces the shape approved in issue #4 (prototypes/demo-seed-data.html on
branch prototype/demo-seed-data), with dates computed relative to `today` so
the fixed three-month report window is always populated.
"""

import asyncio
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts import service as contacts_service
from crm.contacts.schemas import ContactCreate
from crm.core.dates import default_today, shift_month
from crm.core.db import async_session
from crm.opportunities import service as opportunities_service
from crm.opportunities.models import Opportunity, OpportunityStage, OpportunityStatus
from crm.opportunities.schemas import OpportunityCreate
from crm.tasks import service as tasks_service
from crm.tasks.models import TaskType
from crm.tasks.schemas import TaskCreate

LAURA, MARCOS, ELENA, DAVID = "Laura Fernández", "Marcos Ibáñez", "Elena Torres", "David Prieto"

CONTACTS: list[tuple[str, str]] = [
    ("Marta Robles", "Grupo Solvia"),
    ("Iván Castells", "Nortia Logística"),
    ("Rocío Peña", "BancoFácil"),
    ("Álvaro Ruiz", "Talento Digital"),
    ("Sonia Blázquez", "Hidrotec Ingeniería"),
    ("Pablo Escudero", "Vértice Seguros"),
    ("Cristina Nogales", "Muebles Larén"),
    ("Rubén Salgado", "Aeroparts Ibérica"),
    ("Beatriz Ortega", "Clínica Medisur"),
    ("Jorge Villalba", "Cerámicas del Sur"),
    ("Lucía Bermejo", "Retail Norte"),
    ("Óscar Vidal", "Retail Norte"),
    ("Patricia Lamas", "Puerto Digital"),
    ("Andrés Cobo", "Fintel Consulting"),
    ("Nuria Falcón", "Agroexport Levante"),
    ("Diego Marín", "TransEuropa"),
    ("Silvia Reyes", "TransEuropa"),
    ("Carla Espina", "Editorial Aurora"),
    ("Héctor Domínguez", "Energía Verde SL"),
    ("Marina Prats", "Instituto Formativo Delta"),
]

DEAL_TITLES = [
    "Implementación de plataforma",
    "Renovación de contrato",
    "Proyecto de consultoría",
    "Migración de sistemas",
    "Ampliación de licencias",
    "Automatización de procesos",
    "Integración de sistemas",
    "Soporte y mantenimiento",
    "Digitalización de operaciones",
    "Optimización de infraestructura",
]

# proto_id, contact_id (1-based, into CONTACTS), stage, value, owner. Status is always open.
OPEN_OPPORTUNITIES: list[tuple[int, int, OpportunityStage, int | None, str]] = [
    (1, 1, OpportunityStage.NEW, 18000, LAURA),
    (2, 4, OpportunityStage.NEW, 9500, MARCOS),
    (3, 9, OpportunityStage.NEW, 25000, ELENA),
    (4, 15, OpportunityStage.NEW, 14000, DAVID),
    (5, 19, OpportunityStage.NEW, 31000, LAURA),
    (6, 2, OpportunityStage.QUALIFIED, 42000, MARCOS),
    (7, 6, OpportunityStage.QUALIFIED, None, ELENA),
    (8, 11, OpportunityStage.QUALIFIED, 27500, DAVID),
    (9, 17, OpportunityStage.QUALIFIED, 16800, LAURA),
    (10, 3, OpportunityStage.PROPOSAL, 65000, MARCOS),
    (11, 8, OpportunityStage.PROPOSAL, 48000, ELENA),
    (12, 13, OpportunityStage.PROPOSAL, 22000, DAVID),
    (13, 18, OpportunityStage.PROPOSAL, 12500, LAURA),
    (14, 5, OpportunityStage.NEGOTIATION, 89000, MARCOS),
    (15, 12, OpportunityStage.NEGOTIATION, 54000, ELENA),
    (16, 20, OpportunityStage.NEGOTIATION, 19000, DAVID),
]

# proto_id, contact_id, stage, status, value, owner, months_ago, day-of-month.
# day-of-month is always <= 27, so it's valid in every month regardless of when this runs.
CLOSED_PAST_MONTHS: list[
    tuple[int, int, OpportunityStage, OpportunityStatus, int | None, str, int, int]
] = [
    (17, 7, OpportunityStage.NEGOTIATION, OpportunityStatus.WON, 37000, LAURA, 2, 3),
    (18, 10, OpportunityStage.NEGOTIATION, OpportunityStatus.WON, 22500, MARCOS, 2, 11),
    (19, 14, OpportunityStage.PROPOSAL, OpportunityStatus.WON, 15800, ELENA, 2, 18),
    (20, 16, OpportunityStage.NEGOTIATION, OpportunityStatus.WON, 61000, DAVID, 2, 27),
    (21, 1, OpportunityStage.NEW, OpportunityStatus.LOST, 8000, LAURA, 2, 5),
    (22, 9, OpportunityStage.QUALIFIED, OpportunityStatus.LOST, 17500, MARCOS, 2, 14),
    (23, 19, OpportunityStage.PROPOSAL, OpportunityStatus.LOST, 29000, ELENA, 2, 22),
    (24, 2, OpportunityStage.NEGOTIATION, OpportunityStatus.WON, 51000, DAVID, 1, 2),
    (25, 6, OpportunityStage.NEGOTIATION, OpportunityStatus.WON, 33500, LAURA, 1, 10),
    (26, 17, OpportunityStage.PROPOSAL, OpportunityStatus.WON, 24000, MARCOS, 1, 21),
    (27, 11, OpportunityStage.POC, OpportunityStatus.LOST, 19500, ELENA, 1, 8),
    (28, 3, OpportunityStage.NEGOTIATION, OpportunityStatus.LOST, 72000, DAVID, 1, 25),
]

# proto_id, contact_id, stage, status, value, owner, day-of-month.
# Clamped to today's day-of-month at use (see _this_month), so this always lands
# in the current calendar month and never in the future, even run on day 1.
CLOSED_CURRENT_MONTH: list[
    tuple[int, int, OpportunityStage, OpportunityStatus, int | None, str, int]
] = [
    (29, 8, OpportunityStage.NEGOTIATION, OpportunityStatus.WON, 43000, LAURA, 4),
    (30, 13, OpportunityStage.NEGOTIATION, OpportunityStatus.WON, 27800, MARCOS, 9),
    (31, 18, OpportunityStage.NEGOTIATION, OpportunityStatus.WON, 16000, ELENA, 13),
    (32, 5, OpportunityStage.NEW, OpportunityStatus.LOST, 12000, DAVID, 2),
    (33, 20, OpportunityStage.QUALIFIED, OpportunityStatus.LOST, None, LAURA, 7),
    (34, 4, OpportunityStage.NEW, OpportunityStatus.LOST, 6500, MARCOS, 12),
]

# proto_id, contact_id, opportunity proto_id (or None), title, type, owner, due in N days (or None).
PENDING_TASKS: list[tuple[int, int, int | None, str, TaskType, str, int | None]] = [
    (1, 1, 1, "Enviar propuesta técnica inicial", TaskType.EMAIL, LAURA, 2),
    (3, 3, 10, "Preparar demo para comité de compras", TaskType.MEETING, MARCOS, 4),
    (4, 5, 14, "Confirmar fecha de firma de contrato", TaskType.CALL, MARCOS, 1),
    (6, 9, 3, "Agendar reunión técnica con IT", TaskType.MEETING, ELENA, 6),
    (7, 11, 8, "Resolver dudas sobre integración", TaskType.CALL, DAVID, 3),
    (9, 16, None, "Renovación de contrato de mantenimiento", TaskType.OTHER, DAVID, None),
    (10, 18, 13, "Revisar alcance con legal", TaskType.OTHER, LAURA, 8),
    (11, 20, 16, "Enviar propuesta económica revisada", TaskType.EMAIL, DAVID, 5),
]

# proto_id, contact_id, opportunity proto_id (or None), title, type, owner, months_ago, day-of-month.
COMPLETED_PAST_MONTHS: list[tuple[int, int, int | None, str, TaskType, str, int, int]] = [
    (2, 1, None, "Llamada de seguimiento trimestral", TaskType.CALL, LAURA, 1, 20),
    (5, 7, 17, "Enviar factura y kickoff", TaskType.EMAIL, LAURA, 2, 5),
    (8, 14, 19, "Onboarding post-cierre", TaskType.MEETING, ELENA, 2, 20),
]

# proto_id, contact_id, opportunity proto_id (or None), title, type, owner, day-of-month.
COMPLETED_CURRENT_MONTH: list[tuple[int, int, int | None, str, TaskType, str, int]] = [
    (12, 6, 7, "Videollamada de calificación", TaskType.MEETING, ELENA, 10),
]


def _months_ago(today: date, months: int, day: int) -> date:
    return shift_month(today, -months).replace(day=day)


def _this_month(today: date, day: int) -> date:
    """Day-of-month in the current month, clamped to today so it's never in the future."""
    return today.replace(day=min(day, today.day))


def _at_noon(d: date) -> datetime:
    return datetime.combine(d, time(12, 0), tzinfo=UTC)


def _deal_title(proto_id: int, company: str | None) -> str:
    return f"{DEAL_TITLES[(proto_id - 1) % len(DEAL_TITLES)]} — {company}"


async def seed(session: AsyncSession, today: date | None = None) -> None:
    today = today or default_today()

    contacts = [
        await contacts_service.create_contact(session, ContactCreate(name=name, company=company))
        for name, company in CONTACTS
    ]

    opportunities: dict[int, Opportunity] = {}

    for proto_id, contact_id, stage, value, owner in OPEN_OPPORTUNITIES:
        contact = contacts[contact_id - 1]
        opportunities[proto_id] = await opportunities_service.create_opportunity(
            session,
            OpportunityCreate(
                contact_id=contact.id,
                title=_deal_title(proto_id, contact.company),
                value_usd=Decimal(value) if value is not None else None,
                stage=stage,
                owner=owner,
            ),
        )

    for proto_id, contact_id, stage, status, value, owner, months_ago, day in CLOSED_PAST_MONTHS:
        contact = contacts[contact_id - 1]
        opportunity = await opportunities_service.create_opportunity(
            session,
            OpportunityCreate(
                contact_id=contact.id,
                title=_deal_title(proto_id, contact.company),
                value_usd=Decimal(value) if value is not None else None,
                stage=stage,
                status=status,
                owner=owner,
            ),
        )
        opportunity.closed_at = _at_noon(_months_ago(today, months_ago, day))
        opportunities[proto_id] = opportunity

    for proto_id, contact_id, stage, status, value, owner, day in CLOSED_CURRENT_MONTH:
        contact = contacts[contact_id - 1]
        opportunity = await opportunities_service.create_opportunity(
            session,
            OpportunityCreate(
                contact_id=contact.id,
                title=_deal_title(proto_id, contact.company),
                value_usd=Decimal(value) if value is not None else None,
                stage=stage,
                status=status,
                owner=owner,
            ),
        )
        opportunity.closed_at = _at_noon(_this_month(today, day))
        opportunities[proto_id] = opportunity

    await session.commit()

    for proto_id, contact_id, opp_proto_id, title, task_type, owner, due_days in PENDING_TASKS:
        await tasks_service.create_task(
            session,
            TaskCreate(
                contact_id=contacts[contact_id - 1].id,
                opportunity_id=opportunities[opp_proto_id].id if opp_proto_id else None,
                title=title,
                type=task_type,
                owner=owner,
                due_date=today + timedelta(days=due_days) if due_days is not None else None,
            ),
        )

    for (
        proto_id,
        contact_id,
        opp_proto_id,
        title,
        task_type,
        owner,
        months_ago,
        day,
    ) in COMPLETED_PAST_MONTHS:
        task = await tasks_service.create_task(
            session,
            TaskCreate(
                contact_id=contacts[contact_id - 1].id,
                opportunity_id=opportunities[opp_proto_id].id if opp_proto_id else None,
                title=title,
                type=task_type,
                owner=owner,
            ),
        )
        task.completed_at = _at_noon(_months_ago(today, months_ago, day))

    for (
        proto_id,
        contact_id,
        opp_proto_id,
        title,
        task_type,
        owner,
        day,
    ) in COMPLETED_CURRENT_MONTH:
        task = await tasks_service.create_task(
            session,
            TaskCreate(
                contact_id=contacts[contact_id - 1].id,
                opportunity_id=opportunities[opp_proto_id].id if opp_proto_id else None,
                title=title,
                type=task_type,
                owner=owner,
            ),
        )
        task.completed_at = _at_noon(_this_month(today, day))

    await session.commit()


async def main() -> None:
    async with async_session() as session:
        await seed(session)


if __name__ == "__main__":
    asyncio.run(main())
