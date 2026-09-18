def require_non_blank(value: str, field: str, error: type[Exception]) -> str:
    stripped = value.strip()
    if not stripped:
        raise error(f"{field} cannot be empty")
    return stripped


def blank_to_none(value: object) -> object:
    return None if value == "" else value


def require_non_negative(value: object, field: str, error: type[Exception]) -> object:
    if value is not None and value < 0:
        raise error(f"{field} cannot be negative")
    return value
