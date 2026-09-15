from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from crm.contacts.router import router as contacts_api_router
from crm.contacts.views import router as contacts_views_router
from crm.core.errors import HasDependentsError, NotFoundError

BASE_DIR = Path(__file__).parent

app = FastAPI(title="itela CRM")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.include_router(contacts_api_router)
app.include_router(contacts_views_router)


def _is_api_request(request: Request) -> bool:
    return request.url.path.startswith("/api/")


@app.exception_handler(NotFoundError)
async def handle_not_found(request: Request, exc: NotFoundError) -> Response:
    if _is_api_request(request):
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    return RedirectResponse(
        url=request.headers.get("referer") or "/contacts", status_code=303
    )


@app.exception_handler(HasDependentsError)
async def handle_has_dependents(request: Request, exc: HasDependentsError) -> Response:
    if _is_api_request(request):
        return JSONResponse(
            status_code=409,
            content={"detail": "Cannot delete: it still has dependent records"},
        )
    return RedirectResponse(
        url=request.headers.get("referer") or "/contacts", status_code=303
    )
