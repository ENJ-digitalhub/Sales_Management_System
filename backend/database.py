# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.config import Config
from flask import g

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    """Returns the request-scoped DB session, creating one if it doesn't exist."""
    if 'db' not in g:
        g.db = SessionLocal()
    return g.db