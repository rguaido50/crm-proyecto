from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from crm.contacts.router import router as contacts_api_router
from crm.contacts.views import router as contacts_views_router
from crm.core.errors import HasDependentsError, NotFoundError, ValidationError

BASE_DIR = Path(__file__).parent

app = FastAPI(title="itela CRM")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.include_router(contacts_api_router)
app.include_router(contacts_views_router)


def _domain_error_response(request: Request, status_code: int, detail: str) -> Response:
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=status_code, content={"detail": detail})
    return RedirectResponse(url="/contacts", status_code=303)


@app.exception_handler(NotFoundError)
async def handle_not_found(request: Request, exc: NotFoundError) -> Response:
    return _domain_error_response(request, 404, "Not found")


@app.exception_handler(HasDependentsError)
async def handle_has_dependents(request: Request, exc: HasDependentsError) -> Response:
    return _domain_error_response(request, 409, "Cannot delete: it still has dependent records")


@app.exception_handler(ValidationError)
async def handle_validation_error(request: Request, exc: ValidationError) -> Response:
    return _domain_error_response(request, 422, str(exc))
