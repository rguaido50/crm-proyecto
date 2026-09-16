from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from crm.contacts.router import router as contacts_api_router
from crm.contacts.views import router as contacts_views_router
from crm.core.errors import HasDependentsError, NotFoundError, ValidationError
from crm.core.responses import redirect_with_error
from crm.opportunities.router import router as opportunities_api_router
from crm.opportunities.views import router as opportunities_views_router

BASE_DIR = Path(__file__).parent

app = FastAPI(title="itela CRM")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.include_router(contacts_api_router)
app.include_router(contacts_views_router)
app.include_router(opportunities_api_router)
app.include_router(opportunities_views_router)


def _domain_error_response(request: Request, status_code: int, detail: str) -> Response:
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=status_code, content={"detail": detail})
    fallback_url = request.headers.get("referer") or "/contacts"
    return redirect_with_error(fallback_url, detail)


@app.exception_handler(NotFoundError)
async def handle_not_found(request: Request, exc: NotFoundError) -> Response:
    return _domain_error_response(request, 404, "Not found")


@app.exception_handler(HasDependentsError)
async def handle_has_dependents(request: Request, exc: HasDependentsError) -> Response:
    return _domain_error_response(request, 409, "Cannot delete: it still has dependent records")


@app.exception_handler(ValidationError)
async def handle_validation_error(request: Request, exc: ValidationError) -> Response:
    return _domain_error_response(request, 422, str(exc))


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(
    request: Request, exc: RequestValidationError
) -> Response:
    return _domain_error_response(request, 422, "Invalid input")
