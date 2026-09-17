from datetime import UTC, date, datetime


def shift_month(d: date, delta: int) -> date:
    month_index = d.month - 1 + delta
    return date(d.year + month_index // 12, month_index % 12 + 1, 1)


def default_today() -> date:
    return datetime.now(UTC).date()
