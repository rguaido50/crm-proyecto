from httpx import AsyncClient


async def test_pipeline_endpoint_returns_all_five_stage_keys(client: AsyncClient) -> None:
    response = await client.get("/api/reports/pipeline")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"new", "qualified", "poc", "proposal", "negotiation"}
    assert body["new"]["total"] == "0"
    assert body["new"]["count"] == 0


async def test_won_lost_endpoint_returns_three_month_buckets(client: AsyncClient) -> None:
    response = await client.get("/api/reports/won-lost")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    assert set(body[0].keys()) == {"label", "won_total", "lost_total", "won_count", "lost_count"}


async def test_funnel_endpoint_returns_stages_and_win_rate(client: AsyncClient) -> None:
    response = await client.get("/api/reports/funnel")

    assert response.status_code == 200
    body = response.json()
    assert len(body["stages"]) == 5
    assert body["win_rate"] is None
