import re
from decimal import Decimal

_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def require_non_blank(value: str, field: str, error: type[Exception]) -> str:
    stripped = value.strip()
    if not stripped:
        raise error(f"{field} cannot be empty")
    return stripped


def blank_to_none(value: object) -> object:
    return None if value == "" else value


def require_non_negative(
    value: Decimal | None, field: str, error: type[Exception]
) -> Decimal | None:
    if value is not None and value < 0:
        raise error(f"{field} cannot be negative")
    return value


def require_valid_email(value: str | None, field: str, error: type[Exception]) -> str | None:
    if value is not None and not _EMAIL_PATTERN.match(value):
        raise error(f"{field} is not a valid email address")
    return value
