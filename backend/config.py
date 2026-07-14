# backend/config.py
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Config:
    BASE_DIR = Path(__file__).parent.parent.resolve()
    DB_PATH = BASE_DIR / "database" / "shop.db"

    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY not set in environment. Add it to your .env file.")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")

    # Add other configurations as needed for different phases
    # For example, for Phase 9 deployment
    SECRET_KEY = os.getenv("SECRET_KEY") # Flask secret key
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY not set in environment. Add it to your .env file.")
    WAITRESS_PORT = int(os.getenv("WAITRESS_PORT", 5000))
    WAITRESS_HOST = os.getenv("WAITRESS_HOST", "0.0.0.0")
    LOG_FILE = BASE_DIR / "app.log"
    BACKUP_DIR = BASE_DIR / "backups"
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    SYNC_ENABLED = os.getenv("SYNC_ENABLED", "False").lower() in ("true", "1", "t")

    
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True