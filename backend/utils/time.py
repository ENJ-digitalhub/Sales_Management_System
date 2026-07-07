# backend\utils\time.py
from datetime import datetime

def now_utc() -> datetime:
    return datetime.utcnow()
