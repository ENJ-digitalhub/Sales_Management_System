# backend\config.py
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Config:
    base = Path(__file__).parent.parent.resolve()
    DB_PATH = base / "database" / "shop.db"  # build an absolute path to database/shop.db using Path(__file__)

    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        pass
        # raise ValueError("SECRET_KEY not set in environment")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")