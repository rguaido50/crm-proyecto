from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crm.core.dates import default_today, shift_month
from crm.opportunities.models import Opportunity, OpportunityStage, OpportunityStatus
from crm.reports.schemas import FunnelReport, FunnelStage, MonthlyWonLost, PipelineStageReport

_STAGE_ORDER = list(OpportunityStage)
_CLOSED_STATUSES = (OpportunityStatus.WON, OpportunityStatus.LOST)


def _three_month_window(today: date) -> tuple[datetime, datetime, list[date]]:
    month_starts = [shift_month(today, delta) for delta in (-2, -1, 0)]
    window_end_date = shift_month(today, 1)
    window_start = datetime.combine(month_starts[0], datetime.min.time(), tzinfo=UTC)
    window_end = datetime.combine(window_end_date, datetime.min.time(), tzinfo=UTC)
    return window_start, window_end, month_starts


def _as_percentage(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return Decimal("0.0")
    return (Decimal(numerator) / Decimal(denominator) * 100).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )


async def pipeline_by_stage(session: AsyncSession) -> dict[OpportunityStage, PipelineStageReport]:
    result = await session.execute(
        select(Opportunity.stage, Opportunity.value_usd).where(
            Opportunity.status == OpportunityStatus.OPEN
        )
    )
    totals = {stage: Decimal(0) for stage in OpportunityStage}
    counts = {stage: 0 for stage in OpportunityStage}
    unvalued_counts = {stage: 0 for stage in OpportunityStage}
    for stage, value_usd in result.tuples().all():
        counts[stage] += 1
        if value_usd is None:
            unvalued_counts[stage] += 1
        else:
            totals[stage] += value_usd
    return {
        stage: PipelineStageReport(
            stage=stage,
            total=totals[stage],
            count=counts[stage],
            unvalued_count=unvalued_counts[stage],
        )
        for stage in OpportunityStage
    }


async def _closed_deals_in_window(
    session: AsyncSession, today: date
) -> list[tuple[OpportunityStatus, OpportunityStage, Decimal | None, datetime | None]]:
    window_start, window_end, _ = _three_month_window(today)
    result = await session.execute(
        select(
            Opportunity.status, Opportunity.stage, Opportunity.value_usd, Opportunity.closed_at
        ).where(
            Opportunity.status.in_(_CLOSED_STATUSES),
            Opportunity.closed_at >= window_start,
            Opportunity.closed_at < window_end,
        )
    )
    return list(result.tuples().all())


async def won_lost_by_month(
    session: AsyncSession, today: date | None = None
) -> list[MonthlyWonLost]:
    today = today or default_today()
    _, _, month_starts = _three_month_window(today)
    rows = await _closed_deals_in_window(session, today)

    won_totals = {m: Decimal(0) for m in month_starts}
    lost_totals = {m: Decimal(0) for m in month_starts}
    won_counts = {m: 0 for m in month_starts}
    lost_counts = {m: 0 for m in month_starts}
    for status, _stage, value_usd, closed_at in rows:
        assert closed_at is not None, "query filters closed_at IS NOT NULL"
        bucket = date(closed_at.year, closed_at.month, 1)
        if status == OpportunityStatus.WON:
            won_counts[bucket] += 1
            if value_usd is not None:
                won_totals[bucket] += value_usd
        else:
            lost_counts[bucket] += 1
            if value_usd is not None:
                lost_totals[bucket] += value_usd

    return [
        MonthlyWonLost(
            label=month.strftime("%b %Y"),
            won_total=won_totals[month],
            lost_total=lost_totals[month],
            won_count=won_counts[month],
            lost_count=lost_counts[month],
        )
        for month in month_starts
    ]


async def conversion_funnel(session: AsyncSession, today: date | None = None) -> FunnelReport:
    today = today or default_today()
    rows = await _closed_deals_in_window(session, today)

    total = len(rows)
    won = sum(1 for status, *_ in rows if status == OpportunityStatus.WON)
    win_rate = _as_percentage(won, total) if total else None

    stages = []
    for index, stage in enumerate(_STAGE_ORDER):
        count = sum(1 for _, deal_stage, *_ in rows if _STAGE_ORDER.index(deal_stage) >= index)
        stages.append(
            FunnelStage(stage=stage, count=count, percentage=_as_percentage(count, total))
        )
    return FunnelReport(stages=stages, win_rate=win_rate)
