from urllib.parse import quote

from fastapi.responses import RedirectResponse


def redirect_with_error(url: str, error: str | None, *, status_code: int = 303) -> RedirectResponse:
    if error:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}error={quote(error)}"
    return RedirectResponse(url=url, status_code=status_code)
