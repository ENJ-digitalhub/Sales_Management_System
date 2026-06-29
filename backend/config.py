# backend/config.py
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Config:
    base = Path(__file__).parent.parent.resolve()
    DB_PATH = base / "database" / "shop.db"

    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY not set in environment. Add it to your .env file.")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")