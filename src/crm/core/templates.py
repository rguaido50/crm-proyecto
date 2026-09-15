from pathlib import Path

from fastapi.templating import Jinja2Templates

CRM_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=[
        CRM_DIR / "templates",
        CRM_DIR / "contacts" / "templates",
    ]
)
