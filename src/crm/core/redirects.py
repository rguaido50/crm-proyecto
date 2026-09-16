from urllib.parse import quote

from fastapi.responses import RedirectResponse


def contact_redirect(contact_id: int, error: str | None) -> RedirectResponse:
    url = f"/contacts/{contact_id}"
    if error:
        url += f"?error={quote(error)}"
    return RedirectResponse(url=url, status_code=303)
