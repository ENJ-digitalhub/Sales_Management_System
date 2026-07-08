import pytest
from backend.models.models import User, Device
from backend.utils.security import hash_password


def test_sync_push_idempotent(client, session):
    # Create user and login
    user = User(id="test_user_id", name="Test User", username="testuser", password_hash=hash_password("password123"), role="employee")
    session.add(user)
    session.commit()

    login_response = client.post(
        "/auth/login",
        json={
            "username": "testuser",
            "password": "password123",
            "device_name": "Test Device"
        }
    )
    assert login_response.status_code == 200
    token = login_response.get_json()["token"]

    change = {
        "transaction_id": "11111111-1111-1111-1111-111111111111",
        "entity_type": "product",
        "operation": "CREATE",
        "payload": {
            "id": "prod-sync-1",
            "name": "Sync Product",
            "category": "Sync",
            "selling_price": 25.00,
            "cost_price": 15.00,
            "stock_quantity": 5
        }
    }

    first_response = client.post(
        "/sync",
        headers={"Authorization": f"Bearer {token}"},
        json={"changes": [change]}
    )
    assert first_response.status_code == 200
    data = first_response.get_json()
    assert data["success"] is True
    assert data["results"][0]["status"] == "enqueued"

    second_response = client.post(
        "/sync",
        headers={"Authorization": f"Bearer {token}"},
        json={"changes": [change]}
    )
    assert second_response.status_code == 200
    data = second_response.get_json()
    assert data["success"] is True
    assert data["results"][0]["status"] == "synced"
    assert data["results"][0]["transaction_id"] == change["transaction_id"]


def test_sync_contract_endpoints(client, session):
    user = User(id="test_user_id_2", name="Test User 2", username="testuser2", password_hash=hash_password("password123"), role="employee")
    session.add(user)
    session.commit()

    login_response = client.post(
        "/auth/login",
        json={
            "username": "testuser2",
            "password": "password123",
            "device_name": "Test Device 2"
        }
    )
    assert login_response.status_code == 200
    token = login_response.get_json()["token"]

    response = client.get(
        "/sync/pull?last_sync_time=2026-01-01T00:00:00Z",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.get_json()["success"] is True

    response = client.post(
        "/sync/resolve",
        headers={"Authorization": f"Bearer {token}"},
        json={"transaction_id": "does-not-exist", "resolution_payload": {}}
    )
    assert response.status_code == 400
    assert response.get_json()["success"] is False
