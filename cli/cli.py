# cli/cli.py
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.models import Base

base = Path(__file__).parent.parent.resolve()
DB_PATH = base / "database" / "shop.db"  # build an absolute path to database/shop.db using Path(__file__)

engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(bind=engine)

# print(DB_PATH)
class CLI:
    def __init__(self) -> None:
        pass