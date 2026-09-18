import pytest
from playwright.sync_api import Page

pytestmark = pytest.mark.e2e

VIEWS = [
    ("/", "Home"),
    ("/contacts", "Contacts"),
    ("/pipeline", "Pipeline"),
    ("/tasks", "Tasks"),
    ("/reports", "Reports"),
]


@pytest.mark.parametrize("path, heading", VIEWS)
def test_view_loads_without_console_errors(page: Page, path: str, heading: str) -> None:
    console_errors: list[str] = []
    page.on(
        "console",
        lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
    )

    page.goto(path)

    assert page.get_by_role("heading", name=heading, level=1).is_visible()
    # favicon.ico 404 is a known cosmetic gap, not a page failure
    real_errors = [e for e in console_errors if "favicon.ico" not in e]
    assert not real_errors, f"console errors on {path}: {real_errors}"
