from decimal import Decimal
from pathlib import Path

from fastapi.templating import Jinja2Templates

CRM_DIR = Path(__file__).resolve().parent.parent


def _module_template_dirs(base_dir: Path = CRM_DIR) -> list[Path]:
    dirs = sorted(base_dir.glob("*/templates"))
    seen: dict[str, Path] = {}
    for directory in dirs:
        for path in directory.rglob("*.html"):
            name = str(path.relative_to(directory))
            if name in seen:
                raise RuntimeError(
                    f"Template name collision: '{name}' exists in both "
                    f"{seen[name]} and {directory} — Jinja2Templates would silently "
                    "pick whichever comes first. Rename one of them."
                )
            seen[name] = directory
    return dirs


templates = Jinja2Templates(directory=[CRM_DIR / "templates", *_module_template_dirs()])


def currency(value: Decimal | None) -> str:
    return f"${value:.2f}" if value is not None else "—"


templates.env.filters["currency"] = currency
