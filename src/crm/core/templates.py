from decimal import Decimal
from pathlib import Path

from fastapi.templating import Jinja2Templates

CRM_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=[CRM_DIR / "templates", *sorted(CRM_DIR.glob("*/templates"))]
)


def currency(value: Decimal | None) -> str:
    return f"${value:.2f}" if value is not None else "—"


templates.env.filters["currency"] = currency
