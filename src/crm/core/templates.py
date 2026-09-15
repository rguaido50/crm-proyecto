from pathlib import Path

from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, Environment, FileSystemLoader, PrefixLoader

CRM_DIR = Path(__file__).resolve().parent.parent

loader = ChoiceLoader(
    [
        FileSystemLoader(CRM_DIR / "templates"),
        PrefixLoader(
            {
                "contacts": FileSystemLoader(CRM_DIR / "contacts" / "templates"),
            }
        ),
    ]
)

templates = Jinja2Templates(env=Environment(loader=loader, autoescape=True))
