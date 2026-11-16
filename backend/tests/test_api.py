import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app(
        {
            "TESTING": True,
            "MONGO_PERSISTENCE_ENABLED": False,
        }
    )
    return app.test_client()


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {
        "success": True,
        "message": "Backend is running",
    }


@pytest.mark.parametrize(
    "body, content_type",
    [
        ("not-json", "application/json"),
        ("[]", "application/json"),
    ],
)
def test_invalid_request_format(client, body, content_type):
    response = client.post(
        "/api/validate-request",
        data=body,
        content_type=content_type,
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == 400


def test_persistence_status_defaults_to_memory(client):
    response = client.get("/api/persistence/status")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["backend"] == "memory"


def test_persistence_health_defaults_to_memory(client):
    response = client.get("/api/persistence/health")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {
        "success": True,
        "persistence_enabled": False,
        "mongodb_reachable": False,
        "database_configured": True,
        "message": "MongoDB persistence is disabled",
    }


def test_persisted_route_memory_crud(client):
    created = client.post("/api/persistence/routes", json={"name": "Demo route"})
    assert created.status_code == 201
    item = created.get_json()["item"]

    listed = client.get("/api/persistence/routes")
    assert listed.status_code == 200
    assert listed.get_json()["items"][0]["name"] == "Demo route"

    deleted = client.delete(f"/api/persistence/routes/{item['id']}")
    assert deleted.status_code == 200


def test_ordered_route_rejects_duplicate_checkpoints(client):
    response = client.post(
        "/api/routes/calculate",
        json={
            "start": [86.9, 27.9],
            "stops": [[86.95, 27.95], [86.95, 27.95]],
            "destination": [87.1, 28.1],
        },
    )
    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_ordered_route_rejects_checkpoint_matching_start(client):
    response = client.post(
        "/api/routes/calculate",
        json={
            "start": [86.9, 27.9],
            "stops": [[86.9, 27.9]],
            "destination": [87.1, 28.1],
        },
    )
    assert response.status_code == 400
    assert response.get_json()["success"] is False
