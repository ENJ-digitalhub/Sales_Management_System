from flask import g, current_app
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

# Shared Base for all models
Base = declarative_base()


def get_engine():
    """Create SQLAlchemy engine from Flask config."""
    return create_engine(
        current_app.config["SQLALCHEMY_DATABASE_URI"],
        echo=current_app.config.get("SQLALCHEMY_ECHO", False),
    )


def get_db():
    """
    Returns a request-scoped SQLAlchemy session.
    """
    if "db" not in g:
        engine = get_engine()
        Session = scoped_session(
            sessionmaker(
                bind=engine,
                autoflush=False,
                autocommit=False,
                expire_on_commit=False,
            )
        )
        g.db = Session()

    return g.db


def close_db(e=None):
    session = g.pop("db", None)
    if session is not None:
        session.close()


def init_db():
    """
    Create all database tables.
    """
    # Import models here so SQLAlchemy registers them
    import backend.models.models

    engine = get_engine()
    Base.metadata.create_all(bind=engine)