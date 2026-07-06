
import pytest
from backend.models.models import User, Product
from backend.utils.security import hash_password
from decimal import Decimal

@pytest.fixture(scope="function")
def auth_headers(client, session):
    # Create an admin user for testing product management
    hashed_password = hash_password("adminpass")
    admin_user = User(id="admin_user_id", name="Admin User", username="admin", password_hash=hashed_password, role="admin")
    session.add(admin_user)
    session.commit()

    login_response = client.post(
        "/auth/login",
        json={
            "username": "admin",
            "password": "adminpass",
            "device_name": "Test Admin Device"
        }
    )
    token = login_response.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def setup_products(session):
    product1 = Product(
        id="prod1", name="Laptop", category="Electronics",
        selling_price=Decimal("1200.00"), cost_price=Decimal("1000.00"), stock_quantity=10
    )
    product2 = Product(
        id="prod2", name="Mouse", category="Electronics",
        selling_price=Decimal("25.00"), cost_price=Decimal("15.00"), stock_quantity=50
    )
    session.add_all([product1, product2])
    session.commit()
    return product1, product2

def test_create_product(client, auth_headers):
    response = client.post(
        "/products/",
        headers=auth_headers,
        json={
            "name": "Keyboard",
            "category": "Electronics",
            "selling_price": "75.00",
            "cost_price": "50.00",
            "stock_quantity": 30
        }
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert data["product"]["name"] == "Keyboard"

def test_get_product(client, auth_headers, setup_products):
    product1, _ = setup_products
    response = client.get(
        f"/products/{product1.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["product"]["id"] == product1.id

def test_get_all_products(client, auth_headers, setup_products):
    response = client.get(
        "/products/",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert len(data["products"]) == 2

def test_update_product(client, auth_headers, setup_products):
    product1, _ = setup_products
    response = client.put(
        f"/products/{product1.id}",
        headers=auth_headers,
        json={
            "selling_price": "1250.00",
            "stock_quantity": 15
        }
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["product"]["selling_price"] == 1250.00
    assert data["product"]["stock_quantity"] == 15

def test_delete_product(client, auth_headers, setup_products):
    product1, _ = setup_products
    response = client.delete(
        f"/products/{product1.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "deactivated successfully" in data["message"]

    # Verify product is inactive
    response = client.get(
        f"/products/{product1.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["product"]["is_active"] is False
