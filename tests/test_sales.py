
import pytest
from backend.models.models import User, Product, Sale, SaleItem, InventoryLog
from backend.utils.security import hash_password
from decimal import Decimal
from datetime import datetime, timedelta, timezone

@pytest.fixture(scope="function")
def auth_headers(client, session):
    # Create an employee user for testing sales
    hashed_password = hash_password("employeepass")
    employee_user = User(id="employee_user_id", name="Employee User", username="employee", password_hash=hashed_password, role="employee")
    session.add(employee_user)

    # Create an admin user for testing cancellation
    hashed_password_admin = hash_password("adminpass")
    admin_user = User(id="admin_user_id", name="Admin User", username="admin", password_hash=hashed_password_admin, role="admin")
    session.add(admin_user)
    session.commit()

    login_response = client.post(
        "/auth/login",
        json={
            "username": "employee",
            "password": "employeepass",
            "device_name": "Test Employee Device"
        }
    )
    token = login_response.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def admin_auth_headers(client, session):
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
def setup_products_for_sales(session):
    product1 = Product(
        id="prod_sale_1", name="Laptop Pro", category="Electronics",
        selling_price=Decimal("1500.00"), cost_price=Decimal("1200.00"), stock_quantity=10
    )
    product2 = Product(
        id="prod_sale_2", name="Monitor 4K", category="Electronics",
        selling_price=Decimal("400.00"), cost_price=Decimal("300.00"), stock_quantity=5
    )
    session.add_all([product1, product2])
    session.commit()
    return product1, product2

def test_create_sale_success(client, auth_headers, setup_products_for_sales, session):
    product1, product2 = setup_products_for_sales
    initial_stock_p1 = product1.stock_quantity
    initial_stock_p2 = product2.stock_quantity

    sale_data = {
        "items": [
            {"product_id": product1.id, "quantity": 2},
            {"product_id": product2.id, "quantity": 1}
        ],
        "payment_method": "cash"
    }

    response = client.post(
        "/sales/",
        headers=auth_headers,
        json=sale_data
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert "sale" in data
    assert data["sale"]["total_amount"] == float(Decimal("1500.00") * 2 + Decimal("400.00") * 1)
    assert data["sale"]["status"] == "completed"

    # Verify stock deduction
    updated_product1 = session.query(Product).filter_by(id=product1.id).first()
    updated_product2 = session.query(Product).filter_by(id=product2.id).first()
    assert updated_product1.stock_quantity == initial_stock_p1 - 2
    assert updated_product2.stock_quantity == initial_stock_p2 - 1

def test_create_sale_insufficient_stock(client, auth_headers, setup_products_for_sales):
    product1, _ = setup_products_for_sales
    sale_data = {
        "items": [
            {"product_id": product1.id, "quantity": 100} # More than available stock
        ],
        "payment_method": "cash"
    }

    response = client.post(
        "/sales/",
        headers=auth_headers,
        json=sale_data
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert "Insufficient stock" in data["message"]

def test_get_sale_success(client, auth_headers, setup_products_for_sales, session):
    product1, product2 = setup_products_for_sales
    sale_data = {
        "items": [
            {"product_id": product1.id, "quantity": 1}
        ],
        "payment_method": "transfer"
    }
    create_response = client.post("/sales/", headers=auth_headers, json=sale_data)
    sale_id = create_response.get_json()["sale"]["id"]

    response = client.get(
        f"/sales/{sale_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["sale"]["id"] == sale_id
    assert len(data["sale"]["items"]) == 1
    assert data["sale"]["items"][0]["product"]["id"] == product1.id

def test_get_all_sales_success(client, auth_headers, setup_products_for_sales, session):
    product1, _ = setup_products_for_sales
    sale_data_1 = {"items": [{"product_id": product1.id, "quantity": 1}], "payment_method": "cash"}
    sale_data_2 = {"items": [{"product_id": product1.id, "quantity": 2}], "payment_method": "pos"}
    client.post("/sales/", headers=auth_headers, json=sale_data_1)
    client.post("/sales/", headers=auth_headers, json=sale_data_2)

    response = client.get(
        "/sales/",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert len(data["sales"]) >= 2 # May have other sales from other tests

def test_cancel_sale_success_admin(client, admin_auth_headers, setup_products_for_sales, session):
    product1, _ = setup_products_for_sales
    initial_stock = session.query(Product).filter_by(id=product1.id).first().stock_quantity

    sale_data = {
        "items": [
            {"product_id": product1.id, "quantity": 1}
        ],
        "payment_method": "cash"
    }
    create_response = client.post("/sales/", headers=admin_auth_headers, json=sale_data)
    sale_id = create_response.get_json()["sale"]["id"]

    response = client.post(
        f"/sales/{sale_id}/cancel",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "cancelled" in data["message"]

    # Verify sale status and stock restoration
    cancelled_sale = session.query(Sale).filter_by(id=sale_id).first()
    assert cancelled_sale.status == "cancelled"
    updated_product1 = session.query(Product).filter_by(id=product1.id).first()
    assert updated_product1.stock_quantity == initial_stock

def test_cancel_sale_permission_denied_employee(client, auth_headers, setup_products_for_sales, session):
    product1, _ = setup_products_for_sales
    sale_data = {
        "items": [
            {"product_id": product1.id, "quantity": 1}
        ],
        "payment_method": "cash"
    }
    create_response = client.post("/sales/", headers=auth_headers, json=sale_data)
    sale_id = create_response.get_json()["sale"]["id"]

    response = client.post(
        f"/sales/{sale_id}/cancel",
        headers=auth_headers # Employee trying to cancel
    )
    assert response.status_code == 403 # Forbidden
    data = response.get_json()
    assert data["success"] is False
    assert "Permission denied" in data["message"]

def test_edit_sale_success(client, auth_headers, setup_products_for_sales, session):
    product1, product2 = setup_products_for_sales
    initial_stock_p1 = session.query(Product).filter_by(id=product1.id).first().stock_quantity
    initial_stock_p2 = session.query(Product).filter_by(id=product2.id).first().stock_quantity

    # Create an initial sale
    sale_data_initial = {
        "items": [
            {"product_id": product1.id, "quantity": 1}
        ],
        "payment_method": "cash"
    }
    create_response = client.post("/sales/", headers=auth_headers, json=sale_data_initial)
    sale_id = create_response.get_json()["sale"]["id"]

    # Edit the sale
    edited_sale_data = {
        "items": [
            {"product_id": product1.id, "quantity": 2}, # Change quantity
            {"product_id": product2.id, "quantity": 1}  # Add new item
        ],
        "payment_method": "transfer"
    }

    response = client.put(
        f"/sales/{sale_id}",
        headers=auth_headers,
        json=edited_sale_data
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["sale"]["id"] == sale_id
    assert data["sale"]["status"] == "edited"
    assert data["sale"]["payment_method"] == "transfer"
    assert len(data["sale"]["items"]) == 2

    # Verify stock changes: initial sale (1xP1) reverted, then new sale (2xP1, 1xP2) applied
    updated_product1 = session.query(Product).filter_by(id=product1.id).first()
    updated_product2 = session.query(Product).filter_by(id=product2.id).first()
    assert updated_product1.stock_quantity == initial_stock_p1 - 2
    assert updated_product2.stock_quantity == initial_stock_p2 - 1

def test_edit_sale_after_window_employee(client, auth_headers, setup_products_for_sales, session):
    product1, _ = setup_products_for_sales

    # Create an initial sale with a very short editable_until to simulate expired window
    sale_data_initial = {
        "items": [
            {"product_id": product1.id, "quantity": 1}
        ],
        "payment_method": "cash"
    }
    create_response = client.post("/sales/", headers=auth_headers, json=sale_data_initial)
    sale_id = create_response.get_json()["sale"]["id"]

    # Manually set editable_until to past for the created sale
    sale = session.query(Sale).filter_by(id=sale_id).first()
    sale.editable_until = datetime.now(timezone.utc) - timedelta(minutes=1)
    session.add(sale)
    session.commit()

    edited_sale_data = {
        "items": [
            {"product_id": product1.id, "quantity": 1}
        ],
        "payment_method": "transfer"
    }

    response = client.put(
        f"/sales/{sale_id}",
        headers=auth_headers,
        json=edited_sale_data
    )
    assert response.status_code == 403 # Forbidden
    data = response.get_json()
    assert data["success"] is False
    assert "Edit window has closed" in data["message"]
