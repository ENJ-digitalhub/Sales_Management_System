# migrate_sync_queue.py — run once: python migrate_sync_queue.py
import sqlite3
from backend.config import Config

DB_PATH = Config.DB_PATH

EXPECTED_COLUMNS = {
    "conflict_type": "TEXT",
    "result_message": "TEXT",
    "server_sale_id": "TEXT",
    "resolved_by": "TEXT",
    "resolved_at": "TEXT",
    "resolution_note": "TEXT",
}

conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

cur.execute("PRAGMA table_info(sync_queue)")
existing_columns = {row[1] for row in cur.fetchall()}
print("DB path:", DB_PATH)
print("Existing columns:", existing_columns)

for col, col_type in EXPECTED_COLUMNS.items():
    if col not in existing_columns:
        print(f"Adding missing column: {col} ({col_type})")
        cur.execute(f"ALTER TABLE sync_queue ADD COLUMN {col} {col_type}")
    else:
        print(f"Already present: {col}")

conn.commit()
conn.close()
print("Done. Restart Flask now.")