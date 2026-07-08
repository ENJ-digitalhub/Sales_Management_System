
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.config import Config
from backend.models.models import Base
from flask import g

engine = None
SessionLocal = None


def init_db(database_uri: str | None = None):
    """Initialize or reinitialize the SQLAlchemy engine and session factory."""
    global engine, SessionLocal
    if database_uri is None:
        database_uri = Config.SQLALCHEMY_DATABASE_URI

    if engine is not None:
        engine.dispose()

    engine = create_engine(database_uri, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


init_db()


def set_database_uri(database_uri: str):
    """Set the active database URI and rebuild engine/session locals."""
    init_db(database_uri)


def get_db():
    """Returns the request-scoped DB session, creating one if it doesn't exist."""
    if 'db' not in g:
        g.db = SessionLocal()
    return g.db


def create_all_tables():
    Base.metadata.create_all(bind=engine)

