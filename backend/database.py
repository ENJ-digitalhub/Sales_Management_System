from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from backend.config import Config

engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI, 
    connect_args={"check_same_thread": False} if "sqlite" in Config.SQLALCHEMY_DATABASE_URI else {}
)

# Manage a clean scoped session per request thread
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()