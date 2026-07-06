# migrate_sync_queue_2.py — run once: python migrate_sync_queue_2.py
import sqlite3
from backend.config import Config

DB_PATH = Config.DB_PATH

conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

cur.execute("PRAGMA table_info(sync_queue)")
existing_columns = {row[1] for row in cur.fetchall()}
print("DB path:", DB_PATH)
print("Existing columns:", existing_columns)

if "submitted_by" not in existing_columns:
    print("Adding missing column: submitted_by (TEXT)")
    cur.execute("ALTER TABLE sync_queue ADD COLUMN submitted_by TEXT")
else:
    print("Already present: submitted_by")

conn.commit()
conn.close()
print("Done. Restart Flask now.")