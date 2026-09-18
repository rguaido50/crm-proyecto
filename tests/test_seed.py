from datetime import date
from itertools import pairwise

from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts import service as contacts_service
from crm.opportunities import service as opportunities_service
from crm.opportunities.models import OpportunityStage
from crm.reports import service as reports_service
from crm.seed import seed
from crm.tasks import service as tasks_service

FIXED_TODAY = date(2026, 9, 15)


async def test_seed_creates_twenty_contacts(session: AsyncSession) -> None:
    await seed(session, today=FIXED_TODAY)

    contacts = await contacts_service.list_contacts(session)

    assert len(contacts) == 20


async def test_seed_creates_sixteen_open_opportunities_with_poc_empty(
    session: AsyncSession,
) -> None:
    await seed(session, today=FIXED_TODAY)

    board = await opportunities_service.list_open_by_stage(session)

    assert sum(len(opps) for opps in board.values()) == 16
    assert board[OpportunityStage.POC] == []


async def test_seed_pipeline_has_at_least_one_unvalued_opportunity(
    session: AsyncSession,
) -> None:
    await seed(session, today=FIXED_TODAY)

    pipeline = await reports_service.pipeline_by_stage(session)

    assert sum(stage.unvalued_count for stage in pipeline.values()) >= 1


async def test_seed_creates_eighteen_closed_opportunities_inside_the_three_month_window(
    session: AsyncSession,
) -> None:
    await seed(session, today=FIXED_TODAY)

    months = await reports_service.won_lost_by_month(session, FIXED_TODAY)

    assert sum(m.won_count + m.lost_count for m in months) == 18
    assert all(m.won_count + m.lost_count > 0 for m in months)


async def test_seed_funnel_has_a_non_empty_population_and_a_non_increasing_shape(
    session: AsyncSession,
) -> None:
    await seed(session, today=FIXED_TODAY)

    funnel = await reports_service.conversion_funnel(session, FIXED_TODAY)

    assert funnel.win_rate is not None
    counts = [stage.count for stage in funnel.stages]
    assert counts[0] > 0
    assert all(earlier >= later for earlier, later in pairwise(counts))


async def test_seed_creates_twelve_tasks(session: AsyncSession) -> None:
    await seed(session, today=FIXED_TODAY)

    tasks = await tasks_service.list_tasks(session)

    assert len(tasks) == 12


async def test_seed_run_twice_does_not_duplicate_data(session: AsyncSession) -> None:
    await seed(session, today=FIXED_TODAY)
    await seed(session, today=FIXED_TODAY)

    contacts = await contacts_service.list_contacts(session)

    assert len(contacts) == 20


async def test_seed_run_early_in_the_month_keeps_current_month_deals_in_that_bucket(
    session: AsyncSession,
) -> None:
    early_today = date(2026, 3, 3)

    await seed(session, today=early_today)

    months = await reports_service.won_lost_by_month(session, early_today)

    assert months[-1].won_count + months[-1].lost_count == 6
