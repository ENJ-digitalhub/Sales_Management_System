import pytest

from backend.app import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config.update(
        TESTING=True,
    )
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


class DummyResponse:
    def __init__(self, payload=None, status_code=200):
        self.payload = payload or {}
        self.status_code = status_code

    def __iter__(self):
        return iter(())

    def get_json(self):
        return self.payload


def auth_headers(token="test-token"):
    return {"Authorization": f"Bearer {token}"}


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_login_route_exists(client, monkeypatch):
    from backend.controllers.auth_controller import AuthController

    monkeypatch.setattr(
        AuthController,
        "login",
        staticmethod(lambda: ({"success": True, "message": "ok"}, 200)),
    )

    response = client.post("/auth/login", json={"email": "a@test.com", "password": "x"})
    assert response.status_code in (200, 400, 401, 500)


def test_verify_requires_token(client):
    response = client.get("/auth/verify")
    assert response.status_code == 401


def test_logout_requires_token(client):
    response = client.post("/auth/logout")
    assert response.status_code == 401


def test_products_requires_token(client):
    response = client.get("/sales/products")
    assert response.status_code == 401


def test_create_sale_requires_token(client):
    response = client.post("/sales", json={})
    assert response.status_code == 401


def test_get_sale_requires_token(client):
    response = client.get("/sales/1")
    assert response.status_code == 401


def test_edit_sale_requires_token(client):
    response = client.patch("/sales/1", json={})
    assert response.status_code == 401


def test_cancel_sale_requires_token(client):
    response = client.post("/sales/1/cancel")
    assert response.status_code == 401


def test_update_product_requires_token(client):
    response = client.patch("/sales/products/1", json={})
    assert response.status_code == 401