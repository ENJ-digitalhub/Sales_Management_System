# backend/utils/time.py
from datetime import datetime, timezone

def now_utc() -> datetime:
    return datetime.now(timezone.utc)