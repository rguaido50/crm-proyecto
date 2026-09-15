from httpx import AsyncClient


async def test_create_contact_returns_201_with_the_created_row(client: AsyncClient) -> None:
    response = await client.post("/api/contacts", json={"name": "Ada Lovelace"})

    assert response.status_code == 201
    assert response.json()["name"] == "Ada Lovelace"


async def test_get_contact_returns_404_for_a_missing_id(client: AsyncClient) -> None:
    response = await client.get("/api/contacts/999999")

    assert response.status_code == 404


async def test_create_contact_rejects_a_blank_name(client: AsyncClient) -> None:
    response = await client.post("/api/contacts", json={"name": ""})

    assert response.status_code == 422


async def test_update_contact_rejects_an_explicit_null_name(client: AsyncClient) -> None:
    created = await client.post("/api/contacts", json={"name": "Ada Lovelace"})

    response = await client.patch(f"/api/contacts/{created.json()['id']}", json={"name": None})

    assert response.status_code == 422
