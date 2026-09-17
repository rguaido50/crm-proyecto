from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts import service as contacts_service
from crm.contacts.models import Contact
from crm.contacts.schemas import ContactCreate
from crm.opportunities import service as opportunities_service
from crm.opportunities.models import Opportunity, OpportunityStage, OpportunityStatus
from crm.opportunities.schemas import OpportunityCreate
from crm.reports import service

TODAY = date(2026, 3, 15)


async def _make_contact(session: AsyncSession) -> Contact:
    return await contacts_service.create_contact(session, ContactCreate(name="Ada Lovelace"))


async def _make_open_opportunity(
    session: AsyncSession,
    contact_id: int,
    *,
    stage: OpportunityStage = OpportunityStage.NEW,
    value_usd: Decimal | None = None,
) -> Opportunity:
    return await opportunities_service.create_opportunity(
        session,
        OpportunityCreate(
            contact_id=contact_id, title="Deal", owner="Sam", stage=stage, value_usd=value_usd
        ),
    )


async def _make_closed_opportunity(
    session: AsyncSession,
    contact_id: int,
    *,
    status: OpportunityStatus,
    closed_at: datetime,
    stage: OpportunityStage = OpportunityStage.NEGOTIATION,
    value_usd: Decimal | None = None,
) -> Opportunity:
    opportunity = await _make_open_opportunity(
        session, contact_id, stage=stage, value_usd=value_usd
    )
    opportunity.status = status
    opportunity.closed_at = closed_at
    await session.commit()
    await session.refresh(opportunity)
    return opportunity


async def test_pipeline_by_stage_always_includes_all_five_stages_even_when_empty(
    session: AsyncSession,
) -> None:
    contact = await _make_contact(session)
    await _make_open_opportunity(session, contact.id, stage=OpportunityStage.NEW)

    board = await service.pipeline_by_stage(session)

    assert set(board.keys()) == set(OpportunityStage)
    assert board[OpportunityStage.POC].total == 0
    assert board[OpportunityStage.POC].count == 0


async def test_pipeline_by_stage_excludes_a_null_value_from_the_sum_but_counts_it(
    session: AsyncSession,
) -> None:
    contact = await _make_contact(session)
    await _make_open_opportunity(
        session, contact.id, stage=OpportunityStage.QUALIFIED, value_usd=Decimal(1000)
    )
    await _make_open_opportunity(session, contact.id, stage=OpportunityStage.QUALIFIED)

    board = await service.pipeline_by_stage(session)

    stage = board[OpportunityStage.QUALIFIED]
    assert stage.total == Decimal(1000)
    assert stage.count == 2
    assert stage.unvalued_count == 1


async def test_pipeline_by_stage_excludes_won_and_lost_opportunities(
    session: AsyncSession,
) -> None:
    contact = await _make_contact(session)
    await _make_closed_opportunity(
        session,
        contact.id,
        status=OpportunityStatus.WON,
        closed_at=datetime(2026, 3, 1, tzinfo=UTC),
        stage=OpportunityStage.NEW,
        value_usd=Decimal(500),
    )

    board = await service.pipeline_by_stage(session)

    assert board[OpportunityStage.NEW].total == 0
    assert board[OpportunityStage.NEW].count == 0


async def test_won_lost_by_month_includes_a_deal_closed_on_day_one_of_the_earliest_bucket(
    session: AsyncSession,
) -> None:
    contact = await _make_contact(session)
    await _make_closed_opportunity(
        session,
        contact.id,
        status=OpportunityStatus.WON,
        closed_at=datetime(2026, 1, 1, tzinfo=UTC),
        value_usd=Decimal(2000),
    )

    months = await service.won_lost_by_month(session, TODAY)

    assert months[0].label == "Jan 2026"
    assert months[0].won_total == Decimal(2000)
    assert months[0].won_count == 1


async def test_won_lost_by_month_excludes_open_deals(session: AsyncSession) -> None:
    contact = await _make_contact(session)
    await _make_open_opportunity(session, contact.id, value_usd=Decimal(999))

    months = await service.won_lost_by_month(session, TODAY)

    assert sum(m.won_count + m.lost_count for m in months) == 0


async def test_won_lost_by_month_null_value_deal_contributes_zero_but_increments_count(
    session: AsyncSession,
) -> None:
    contact = await _make_contact(session)
    await _make_closed_opportunity(
        session,
        contact.id,
        status=OpportunityStatus.LOST,
        closed_at=datetime(2026, 3, 10, tzinfo=UTC),
    )

    months = await service.won_lost_by_month(session, TODAY)

    march = months[-1]
    assert march.lost_count == 1
    assert march.lost_total == Decimal(0)


async def test_won_lost_by_month_renders_empty_bucket_for_a_month_with_no_closings(
    session: AsyncSession,
) -> None:
    months = await service.won_lost_by_month(session, TODAY)

    assert [m.label for m in months] == ["Jan 2026", "Feb 2026", "Mar 2026"]
    assert all(m.won_count == 0 and m.lost_count == 0 for m in months)


async def test_conversion_funnel_with_empty_population_renders_zero_bars_and_none_win_rate(
    session: AsyncSession,
) -> None:
    funnel = await service.conversion_funnel(session, TODAY)

    assert all(stage.count == 0 and stage.percentage == 0 for stage in funnel.stages)
    assert funnel.win_rate is None


async def test_conversion_funnel_deal_lost_at_new_appears_only_in_the_first_bar(
    session: AsyncSession,
) -> None:
    contact = await _make_contact(session)
    await _make_closed_opportunity(
        session,
        contact.id,
        status=OpportunityStatus.LOST,
        closed_at=datetime(2026, 3, 5, tzinfo=UTC),
        stage=OpportunityStage.NEW,
    )

    funnel = await service.conversion_funnel(session, TODAY)

    by_stage = {stage.stage: stage.count for stage in funnel.stages}
    assert by_stage[OpportunityStage.NEW] == 1
    assert by_stage[OpportunityStage.QUALIFIED] == 0
    assert by_stage[OpportunityStage.POC] == 0
    assert by_stage[OpportunityStage.PROPOSAL] == 0
    assert by_stage[OpportunityStage.NEGOTIATION] == 0


async def test_conversion_funnel_deal_won_at_proposal_appears_in_first_four_bars_not_fifth(
    session: AsyncSession,
) -> None:
    contact = await _make_contact(session)
    await _make_closed_opportunity(
        session,
        contact.id,
        status=OpportunityStatus.WON,
        closed_at=datetime(2026, 3, 5, tzinfo=UTC),
        stage=OpportunityStage.PROPOSAL,
    )

    funnel = await service.conversion_funnel(session, TODAY)

    by_stage = {stage.stage: stage.count for stage in funnel.stages}
    assert by_stage[OpportunityStage.NEW] == 1
    assert by_stage[OpportunityStage.QUALIFIED] == 1
    assert by_stage[OpportunityStage.POC] == 1
    assert by_stage[OpportunityStage.PROPOSAL] == 1
    assert by_stage[OpportunityStage.NEGOTIATION] == 0


async def test_conversion_funnel_win_rate_is_count_won_over_count_closed(
    session: AsyncSession,
) -> None:
    contact = await _make_contact(session)
    await _make_closed_opportunity(
        session,
        contact.id,
        status=OpportunityStatus.WON,
        closed_at=datetime(2026, 3, 1, tzinfo=UTC),
    )
    await _make_closed_opportunity(
        session,
        contact.id,
        status=OpportunityStatus.WON,
        closed_at=datetime(2026, 3, 2, tzinfo=UTC),
    )
    await _make_closed_opportunity(
        session,
        contact.id,
        status=OpportunityStatus.LOST,
        closed_at=datetime(2026, 3, 3, tzinfo=UTC),
    )

    funnel = await service.conversion_funnel(session, TODAY)

    assert funnel.win_rate == Decimal("66.7")


async def test_conversion_funnel_ignores_deals_outside_the_three_month_window(
    session: AsyncSession,
) -> None:
    contact = await _make_contact(session)
    await _make_closed_opportunity(
        session,
        contact.id,
        status=OpportunityStatus.WON,
        closed_at=datetime(2025, 12, 31, tzinfo=UTC),
    )

    funnel = await service.conversion_funnel(session, TODAY)

    assert funnel.win_rate is None
