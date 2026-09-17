from fastapi.testclient import TestClient

from crm.main import app


def test_app_boots_and_responds() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200


def test_domain_not_found_error_returns_json_on_api_paths() -> None:
    client = TestClient(app)

    response = client.get("/api/contacts/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not found"}


def test_domain_not_found_error_redirects_with_the_message_on_view_paths() -> None:
    client = TestClient(app, follow_redirects=False)

    response = client.get("/contacts/999999")

    assert response.status_code == 303
    assert response.headers["location"] == "/contacts?error=Not%20found"
