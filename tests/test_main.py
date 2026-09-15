from fastapi.testclient import TestClient

from crm.main import app


def test_app_boots_and_responds() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
