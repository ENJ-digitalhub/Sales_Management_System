from flask import g
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

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

def get_db():
    """
    Returns the current request's SQLAlchemy session.

    Usage:
        session = get_db()
    """
    if "db" not in g:
        g.db = SessionLocal()

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