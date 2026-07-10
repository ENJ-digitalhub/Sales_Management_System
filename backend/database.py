<<<<<<< HEAD
=======

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.config import Config
from backend.models.models import Base
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
from flask import g
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

<<<<<<< HEAD
from backend.config import Config

# ------------------------------------------------------------------
# Database Engine
# ------------------------------------------------------------------

engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
    future=True,
)

# ------------------------------------------------------------------
# Session Factory
# ------------------------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# ------------------------------------------------------------------
# Shared Declarative Base
# ------------------------------------------------------------------

Base = declarative_base()


# ------------------------------------------------------------------
# Request-scoped Session
# ------------------------------------------------------------------
=======
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

>>>>>>> a9333a422bf619f612b4742acd01eac2428da808

def get_db():
    """
    Returns the current request's SQLAlchemy session.

    Usage:
        session = get_db()
    """
    if "db" not in g:
        g.db = SessionLocal()
<<<<<<< HEAD

    return g.db


def close_db(e=None):
    """
    Closes the current request session.
    Register this with:

        app.teardown_appcontext(close_db)
    """
    session = g.pop("db", None)

    if session is not None:
        session.close()


# ------------------------------------------------------------------
# Create Tables
# ------------------------------------------------------------------

def init_db():
    """
    Creates all database tables.
    """
    from backend.models.models import (
        User,
        Device,
        Product,
        Sale,
        SaleItem,
        InventoryLog,
        SyncQueue,
        AuditLog,
        Purchase,
        PurchaseItem,
    )

    Base.metadata.create_all(bind=engine)
=======
    return g.db


def create_all_tables():
    Base.metadata.create_all(bind=engine)

>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
