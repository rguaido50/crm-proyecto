from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from crm.core.templates import templates

router = APIRouter(tags=["reports-views"])


@router.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "reports.html", {})
