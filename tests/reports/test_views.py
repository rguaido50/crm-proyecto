from httpx import AsyncClient


async def test_reports_page_shows_all_three_chart_canvases(client: AsyncClient) -> None:
    response = await client.get("/reports")

    assert response.status_code == 200
    assert 'id="pipeline-chart"' in response.text
    assert 'id="won-lost-chart"' in response.text
    assert 'id="funnel-chart"' in response.text
