from httpx import AsyncClient


async def test_create_opportunity_returns_201_with_the_created_row(client: AsyncClient) -> None:
    contact = await client.post("/api/contacts", json={"name": "Ada Lovelace"})

    response = await client.post(
        "/api/opportunities",
        json={"contact_id": contact.json()["id"], "title": "Deal", "owner": "Sam"},
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Deal"


async def test_create_opportunity_rejects_a_missing_contact_id(client: AsyncClient) -> None:
    response = await client.post("/api/opportunities", json={"title": "Deal", "owner": "Sam"})

    assert response.status_code == 422


async def test_update_opportunity_to_lost_returns_closed_at_populated(
    client: AsyncClient,
) -> None:
    contact = await client.post("/api/contacts", json={"name": "Ada Lovelace"})
    created = await client.post(
        "/api/opportunities",
        json={"contact_id": contact.json()["id"], "title": "Deal", "owner": "Sam"},
    )

    response = await client.patch(
        f"/api/opportunities/{created.json()['id']}", json={"status": "lost"}
    )

    assert response.status_code == 200
    assert response.json()["closed_at"] is not None


async def test_create_opportunity_rejects_a_title_over_the_length_limit(
    client: AsyncClient,
) -> None:
    contact = await client.post("/api/contacts", json={"name": "Ada Lovelace"})

    response = await client.post(
        "/api/opportunities",
        json={"contact_id": contact.json()["id"], "title": "x" * 201, "owner": "Sam"},
    )

    assert response.status_code == 422


async def test_create_opportunity_rejects_an_owner_over_the_length_limit(
    client: AsyncClient,
) -> None:
    contact = await client.post("/api/contacts", json={"name": "Ada Lovelace"})

    response = await client.post(
        "/api/opportunities",
        json={"contact_id": contact.json()["id"], "title": "Deal", "owner": "x" * 101},
    )

    assert response.status_code == 422


async def test_list_open_by_stage_includes_a_known_stage_key(client: AsyncClient) -> None:
    response = await client.get("/api/opportunities")

    assert response.status_code == 200
    assert "poc" in response.json()
