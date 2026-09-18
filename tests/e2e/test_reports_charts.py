import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

CHART_IDS = ("pipeline-chart", "won-lost-chart", "funnel-chart")
API_PATHS = ("/api/reports/pipeline", "/api/reports/won-lost", "/api/reports/funnel")


def test_reports_page_renders_all_charts(page: Page) -> None:
    responses = []
    page.on("response", lambda response: responses.append(response))

    page.goto("/reports")
    page.wait_for_load_state("networkidle")

    for chart_id in CHART_IDS:
        expect(page.locator(f"#{chart_id}")).to_be_visible()

    for api_path in API_PATHS:
        matches = [r for r in responses if api_path in r.url]
        assert matches, f"no request made to {api_path}"
        assert matches[-1].status == 200
