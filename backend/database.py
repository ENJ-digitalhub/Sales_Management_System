
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from backend.config import Config
from backend.models.models import Base
from flask import g

# Use the database URL from Config
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Returns the request-scoped DB session, creating one if it doesn't exist."""
    if 'db' not in g:
        g.db = SessionLocal()
    return g.db

def create_all_tables():
    Base.metadata.create_all(bind=engine)

