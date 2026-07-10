import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Config:
<<<<<<< HEAD
    BASE_DIR = Path(__file__).resolve().parent.parent
    INSTANCE_DIR = BASE_DIR / "instance"
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Force absolute path + forward slashes + 4 slashes for Windows
    DB_PATH = (INSTANCE_DIR / "shop.db").resolve()
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH.as_posix()}"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
=======
    BASE_DIR = Path(__file__).parent.parent.resolve()
    DB_PATH = BASE_DIR / "database" / "shop.db"

>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    if not JWT_SECRET_KEY:
<<<<<<< HEAD
        raise ValueError("JWT_SECRET_KEY not set in .env")
=======
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
    
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
