import os
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
