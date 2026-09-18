import re
import uuid

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def test_complete_task_moves_it_to_activity_history(page: Page) -> None:
    # Tasks can't be deleted (contacts.tasks FK is ON DELETE RESTRICT), so this
    # test creates its own throwaway contact + task instead of touching seed data,
    # and leaves them behind for the next `python -m crm.seed` reset to clear.
    contact_name = f"E2E Task Contact {uuid.uuid4().hex[:8]}"
    task_title = f"E2E task {uuid.uuid4().hex[:8]}"

    page.goto("/contacts")
    page.get_by_role("button", name="+ New Contact").click()
    page.fill("#name", contact_name)
    page.get_by_role("button", name="Create Contact").click()
    page.get_by_role("link", name=contact_name).click()

    page.get_by_role("button", name="+ New Task").click()
    page.fill("#task-title", task_title)
    page.select_option("#task-type", "call")
    page.fill("#task-owner", "E2E Suite")
    page.get_by_role("button", name="Create Task").click()

    expect(page.get_by_text(task_title)).to_be_visible()

    page.goto("/tasks")
    task_row = page.get_by_role("row", name=task_title)
    task_row.get_by_role("button", name="Complete").click()

    expect(page).to_have_url(re.compile(r"/contacts/\d+$"))
    expect(page.get_by_role("heading", name=contact_name)).to_be_visible()
    activity_row = page.get_by_role("row", name=task_title)
    expect(activity_row).to_contain_text("call")
