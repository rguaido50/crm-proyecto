from httpx import AsyncClient


async def test_create_task_returns_201_with_the_created_row(client: AsyncClient) -> None:
    contact = await client.post("/api/contacts", json={"name": "Ada Lovelace"})

    response = await client.post(
        "/api/tasks",
        json={
            "contact_id": contact.json()["id"],
            "title": "Follow up call",
            "type": "call",
            "owner": "Sam",
        },
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Follow up call"


async def test_create_task_rejects_a_missing_contact_id(client: AsyncClient) -> None:
    response = await client.post(
        "/api/tasks", json={"title": "Follow up call", "type": "call", "owner": "Sam"}
    )

    assert response.status_code == 422


async def test_create_task_rejects_a_title_over_the_length_limit(client: AsyncClient) -> None:
    contact = await client.post("/api/contacts", json={"name": "Ada Lovelace"})

    response = await client.post(
        "/api/tasks",
        json={
            "contact_id": contact.json()["id"],
            "title": "x" * 201,
            "type": "call",
            "owner": "Sam",
        },
    )

    assert response.status_code == 422


async def test_create_task_rejects_an_owner_over_the_length_limit(client: AsyncClient) -> None:
    contact = await client.post("/api/contacts", json={"name": "Ada Lovelace"})

    response = await client.post(
        "/api/tasks",
        json={
            "contact_id": contact.json()["id"],
            "title": "Follow up call",
            "type": "call",
            "owner": "x" * 101,
        },
    )

    assert response.status_code == 422


async def test_create_task_rejects_a_description_over_the_length_limit(
    client: AsyncClient,
) -> None:
    contact = await client.post("/api/contacts", json={"name": "Ada Lovelace"})

    response = await client.post(
        "/api/tasks",
        json={
            "contact_id": contact.json()["id"],
            "title": "Follow up call",
            "type": "call",
            "owner": "Sam",
            "description": "x" * 2001,
        },
    )

    assert response.status_code == 422


async def test_complete_task_returns_completed_at_populated(client: AsyncClient) -> None:
    contact = await client.post("/api/contacts", json={"name": "Ada Lovelace"})
    created = await client.post(
        "/api/tasks",
        json={
            "contact_id": contact.json()["id"],
            "title": "Follow up call",
            "type": "call",
            "owner": "Sam",
        },
    )

    response = await client.patch(f"/api/tasks/{created.json()['id']}")

    assert response.status_code == 200
    assert response.json()["completed_at"] is not None


async def test_list_tasks_returns_200(client: AsyncClient) -> None:
    response = await client.get("/api/tasks")

    assert response.status_code == 200
