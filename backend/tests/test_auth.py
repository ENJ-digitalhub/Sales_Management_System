
import pytest
from flask import Flask
from backend.config import Config
from backend.database import Base, engine, SessionLocal
from backend.models.models import User, Device
from backend.utils.security import hash_password
from backend.app import create_app

@pytest.fixture(scope="module")
def app():
    app = create_app(config_class=Config)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        Base.metadata.create_all(bind=engine)
        yield app
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(app):
    return app.test_client()

@pytest.fixture(scope="function")
def session(app):
    with app.app_context():
        db = SessionLocal()
        yield db
        db.rollback()
        db.close()

@pytest.fixture(scope="function")
def setup_users(session):
    # Create a test user
    hashed_password = hash_password("password123")
    user = User(id="test_user_id", name="Test User", username="testuser", password_hash=hashed_password, role="employee")
    session.add(user)
    session.commit()
    return user

def test_register_user(client, session):
    response = client.post(
        "/auth/register",
        json={
            "name": "New User",
            "username": "newuser",
            "password": "newpassword",
            "role": "employee"
        }
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert "user" in data
    assert data["user"]["username"] == "newuser"

    user = session.query(User).filter_by(username="newuser").first()
    assert user is not None

def test_login_success(client, setup_users):
    response = client.post(
        "/auth/login",
        json={
            "username": "testuser",
            "password": "password123",
            "device_name": "Test Device"
        }
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "token" in data
    assert "user" in data
    assert data["user"]["username"] == "testuser"

def test_login_invalid_credentials(client, setup_users):
    response = client.post(
        "/auth/login",
        json={
            "username": "testuser",
            "password": "wrongpassword",
            "device_name": "Test Device"
        }
    )
    assert response.status_code == 401
    data = response.get_json()
    assert data["success"] is False
    assert "Invalid username or password" in data["message"]

def test_verify_token_success(client, setup_users):
    login_response = client.post(
        "/auth/login",
        json={
            "username": "testuser",
            "password": "password123",
            "device_name": "Test Device"
        }
    )
    token = login_response.get_json()["token"]

    response = client.get(
        "/auth/verify",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["valid"] is True
    assert data["user"]["username"] == "testuser"

def test_verify_token_invalid(client):
    response = client.get(
        "/auth/verify",
        headers={
            "Authorization": "Bearer invalid_token"
        }
    )
    assert response.status_code == 200 # Token verification returns valid: false, not 401
    data = response.get_json()
    assert data["valid"] is False

def test_logout_success(client, setup_users, session):
    login_response = client.post(
        "/auth/login",
        json={
            "username": "testuser",
            "password": "password123",
            "device_name": "Test Device"
        }
    )
    token = login_response.get_json()["token"]
    device_id = login_response.get_json()["device_id"]

    response = client.post(
        "/auth/logout",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True

    # Verify device is deactivated
    device = session.query(Device).filter_by(id=device_id).first()
    assert device.is_active is False

