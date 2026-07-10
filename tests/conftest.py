import os
<<<<<<< HEAD
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app import create_app
from backend.config import TestingConfig
from backend.database import get_db
from backend.models.models import Product

@pytest.fixture(scope="session")
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        yield app

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def db_session(app):
    session = get_db()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture()
def auth_headers():
    return {
        "Authorization": "Bearer YOUR_EMPLOYEE_TOKEN"
    }

@pytest.fixture()
def manager_auth_headers():
    return {
        "Authorization": "Bearer YOUR_MANAGER_TOKEN"
    }

@pytest.fixture()
def seeded_product(db_session):
    product = Product(
        id="test-product-1",
        name="Test Product",
        category="Test",
        selling_price=1000,
        cost_price=700,
        stock_quantity=100,
        is_active=1
    )
    db_session.add(product)
    db_session.commit()
    return product
=======
import tempfile
import pytest
import backend.database as database
from backend.config import Config
from backend.app import create_app


@pytest.fixture(scope="function")
def app():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        class TestConfig(Config):
            TESTING = True
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

        app = create_app(config_class=TestConfig)
        with app.app_context():
            database.Base.metadata.create_all(bind=database.engine)
            yield app
    finally:
        database.Base.metadata.drop_all(bind=database.engine)
        try:
            database.engine.dispose()
        except Exception:
            pass
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def session(app):
    db = database.SessionLocal()
    yield db
    try:
        db.rollback()
    except Exception:
        pass
    db.close()
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
