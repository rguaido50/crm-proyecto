import re
import uuid

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def test_create_and_delete_contact(page: Page) -> None:
    name = f"E2E Test {uuid.uuid4().hex[:8]}"

    page.goto("/contacts")
    page.get_by_role("button", name="+ New Contact").click()
    page.fill("#name", name)
    page.fill("#company", "E2E Test Co")
    page.get_by_role("button", name="Create Contact").click()

    contact_link = page.get_by_role("link", name=name)
    expect(contact_link).to_be_visible()
    contact_link.click()

    expect(page.get_by_role("heading", name=name)).to_be_visible()
    page.get_by_role("button", name="Delete").click()

    expect(page).to_have_url(re.compile(r"/contacts$"))
    expect(page.get_by_role("link", name=name)).to_have_count(0)
