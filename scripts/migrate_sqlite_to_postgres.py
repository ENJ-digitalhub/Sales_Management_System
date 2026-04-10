import os
import sqlite3
from pathlib import Path

import psycopg


TABLES_WITH_SERIAL_IDS = (
    "users",
    "product",
    "transactions",
    "notifications",
    "inventory_logs",
    "notification_reads",
    "transaction_audit_logs",
)


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and (
            (value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")
        ):
            value = value[1:-1]
        os.environ.setdefault(key, value)


def map_foreign_id(id_map, value):
    if value is None:
        return None
    return id_map.get(value, value)


def reset_serial_sequences(pg_conn) -> None:
    with pg_conn.cursor() as cur:
        for table_name in TABLES_WITH_SERIAL_IDS:
            cur.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
            max_id = cur.fetchone()[0]
            if max_id > 0:
                cur.execute(
                    f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table_name}', 'id'),
                        %s,
                        true
                    )
                    """,
                    (max_id,),
                )
                continue
            cur.execute(
                f"""
                SELECT setval(
                    pg_get_serial_sequence('{table_name}', 'id'),
                    1,
                    false
                )
                """
            )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    load_env_file(repo_root / ".env")

    sqlite_path = repo_root / "data" / "main.db"
    database_url = os.getenv("DATABASE_URL", "").strip()

    if not sqlite_path.exists():
        raise FileNotFoundError(f"SQLite DB not found at: {sqlite_path}")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Set it in .env first.")

    sqlite_conn = sqlite3.connect(str(sqlite_path))
    sqlite_conn.row_factory = sqlite3.Row

    try:
        with psycopg.connect(database_url, connect_timeout=10) as pg_conn:
            with pg_conn.cursor() as pg_cur:
                # Load existing unique keys so we can map old ids to canonical Postgres ids.
                pg_cur.execute("SELECT id, username FROM users")
                existing_users_by_username = {row[1]: row[0] for row in pg_cur.fetchall() if row[1]}

                pg_cur.execute("SELECT id, name FROM product")
                existing_products_by_name = {row[1]: row[0] for row in pg_cur.fetchall() if row[1]}

                user_id_map = {}
                product_id_map = {}

                sqlite_cur = sqlite_conn.cursor()

                # Users
                sqlite_cur.execute(
                    """
                    SELECT id, first_name, last_name, email, username, password, role, approval_status,
                           is_active, account_name, account_owner_name, bank_name, account_address,
                           phone, image_path, created_at
                    FROM users
                    ORDER BY id
                    """
                )
                for row in sqlite_cur.fetchall():
                    username = row["username"]
                    if username and username in existing_users_by_username:
                        target_id = existing_users_by_username[username]
                        pg_cur.execute(
                            """
                            UPDATE users
                            SET first_name=%s, last_name=%s, email=%s, password=%s, role=%s,
                                approval_status=%s, is_active=%s, account_name=%s,
                                account_owner_name=%s, bank_name=%s, account_address=%s,
                                phone=%s, image_path=%s, created_at=%s
                            WHERE id=%s
                            """,
                            (
                                row["first_name"],
                                row["last_name"],
                                row["email"],
                                row["password"],
                                row["role"],
                                row["approval_status"],
                                row["is_active"],
                                row["account_name"],
                                row["account_owner_name"],
                                row["bank_name"],
                                row["account_address"],
                                row["phone"],
                                row["image_path"],
                                row["created_at"],
                                target_id,
                            ),
                        )
                    else:
                        target_id = row["id"]
                        pg_cur.execute(
                            """
                            INSERT INTO users (
                                id, first_name, last_name, email, username, password, role,
                                approval_status, is_active, account_name, account_owner_name,
                                bank_name, account_address, phone, image_path, created_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                first_name=EXCLUDED.first_name,
                                last_name=EXCLUDED.last_name,
                                email=EXCLUDED.email,
                                username=EXCLUDED.username,
                                password=EXCLUDED.password,
                                role=EXCLUDED.role,
                                approval_status=EXCLUDED.approval_status,
                                is_active=EXCLUDED.is_active,
                                account_name=EXCLUDED.account_name,
                                account_owner_name=EXCLUDED.account_owner_name,
                                bank_name=EXCLUDED.bank_name,
                                account_address=EXCLUDED.account_address,
                                phone=EXCLUDED.phone,
                                image_path=EXCLUDED.image_path,
                                created_at=EXCLUDED.created_at
                            """,
                            (
                                row["id"],
                                row["first_name"],
                                row["last_name"],
                                row["email"],
                                row["username"],
                                row["password"],
                                row["role"],
                                row["approval_status"],
                                row["is_active"],
                                row["account_name"],
                                row["account_owner_name"],
                                row["bank_name"],
                                row["account_address"],
                                row["phone"],
                                row["image_path"],
                                row["created_at"],
                            ),
                        )
                        if username:
                            existing_users_by_username[username] = target_id
                    user_id_map[row["id"]] = target_id

                # Products
                sqlite_cur.execute(
                    """
                    SELECT id, name, price, quantity, image_path, created_at
                    FROM product
                    ORDER BY id
                    """
                )
                for row in sqlite_cur.fetchall():
                    name = row["name"]
                    if name and name in existing_products_by_name:
                        target_id = existing_products_by_name[name]
                        pg_cur.execute(
                            """
                            UPDATE product
                            SET price=%s, quantity=%s, image_path=%s, created_at=%s
                            WHERE id=%s
                            """,
                            (
                                row["price"],
                                row["quantity"],
                                row["image_path"],
                                row["created_at"],
                                target_id,
                            ),
                        )
                    else:
                        target_id = row["id"]
                        pg_cur.execute(
                            """
                            INSERT INTO product (id, name, price, quantity, image_path, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                name=EXCLUDED.name,
                                price=EXCLUDED.price,
                                quantity=EXCLUDED.quantity,
                                image_path=EXCLUDED.image_path,
                                created_at=EXCLUDED.created_at
                            """,
                            (
                                row["id"],
                                row["name"],
                                row["price"],
                                row["quantity"],
                                row["image_path"],
                                row["created_at"],
                            ),
                        )
                        if name:
                            existing_products_by_name[name] = target_id
                    product_id_map[row["id"]] = target_id

                # Transactions
                sqlite_cur.execute(
                    """
                    SELECT id, user_id, product_id, amount, quantity, type, status, customer_name,
                           invoice_path, proof_path, created_at
                    FROM transactions
                    ORDER BY id
                    """
                )
                for row in sqlite_cur.fetchall():
                    pg_cur.execute(
                        """
                        INSERT INTO transactions (
                            id, user_id, product_id, amount, quantity, type, status, customer_name,
                            invoice_path, proof_path, created_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            user_id=EXCLUDED.user_id,
                            product_id=EXCLUDED.product_id,
                            amount=EXCLUDED.amount,
                            quantity=EXCLUDED.quantity,
                            type=EXCLUDED.type,
                            status=EXCLUDED.status,
                            customer_name=EXCLUDED.customer_name,
                            invoice_path=EXCLUDED.invoice_path,
                            proof_path=EXCLUDED.proof_path,
                            created_at=EXCLUDED.created_at
                        """,
                        (
                            row["id"],
                            map_foreign_id(user_id_map, row["user_id"]),
                            map_foreign_id(product_id_map, row["product_id"]),
                            row["amount"],
                            row["quantity"],
                            row["type"],
                            row["status"],
                            row["customer_name"],
                            row["invoice_path"],
                            row["proof_path"],
                            row["created_at"],
                        ),
                    )

                # Notifications
                sqlite_cur.execute(
                    """
                    SELECT id, actor_user_id, target_user_id, type, message, created_at
                    FROM notifications
                    ORDER BY id
                    """
                )
                for row in sqlite_cur.fetchall():
                    pg_cur.execute(
                        """
                        INSERT INTO notifications (id, actor_user_id, target_user_id, type, message, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            actor_user_id=EXCLUDED.actor_user_id,
                            target_user_id=EXCLUDED.target_user_id,
                            type=EXCLUDED.type,
                            message=EXCLUDED.message,
                            created_at=EXCLUDED.created_at
                        """,
                        (
                            row["id"],
                            map_foreign_id(user_id_map, row["actor_user_id"]),
                            map_foreign_id(user_id_map, row["target_user_id"]),
                            row["type"],
                            row["message"],
                            row["created_at"],
                        ),
                    )

                # Inventory logs
                sqlite_cur.execute(
                    """
                    SELECT id, product_id, user_id, action, quantity_change, reason, details, created_at
                    FROM inventory_logs
                    ORDER BY id
                    """
                )
                for row in sqlite_cur.fetchall():
                    pg_cur.execute(
                        """
                        INSERT INTO inventory_logs (
                            id, product_id, user_id, action, quantity_change, reason, details, created_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            product_id=EXCLUDED.product_id,
                            user_id=EXCLUDED.user_id,
                            action=EXCLUDED.action,
                            quantity_change=EXCLUDED.quantity_change,
                            reason=EXCLUDED.reason,
                            details=EXCLUDED.details,
                            created_at=EXCLUDED.created_at
                        """,
                        (
                            row["id"],
                            map_foreign_id(product_id_map, row["product_id"]),
                            map_foreign_id(user_id_map, row["user_id"]),
                            row["action"],
                            row["quantity_change"],
                            row["reason"],
                            row["details"],
                            row["created_at"],
                        ),
                    )

                # Notification reads
                sqlite_cur.execute(
                    """
                    SELECT id, user_id, activity_type, activity_id, read_at
                    FROM notification_reads
                    ORDER BY id
                    """
                )
                for row in sqlite_cur.fetchall():
                    pg_cur.execute(
                        """
                        INSERT INTO notification_reads (id, user_id, activity_type, activity_id, read_at)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (user_id, activity_type, activity_id) DO UPDATE SET
                            read_at=EXCLUDED.read_at
                        """,
                        (
                            row["id"],
                            map_foreign_id(user_id_map, row["user_id"]),
                            row["activity_type"],
                            row["activity_id"],
                            row["read_at"],
                        ),
                    )

                # Transaction audit logs
                sqlite_cur.execute(
                    """
                    SELECT id, transaction_id, user_id, action, payload, created_at
                    FROM transaction_audit_logs
                    ORDER BY id
                    """
                )
                for row in sqlite_cur.fetchall():
                    pg_cur.execute(
                        """
                        INSERT INTO transaction_audit_logs (id, transaction_id, user_id, action, payload, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            transaction_id=EXCLUDED.transaction_id,
                            user_id=EXCLUDED.user_id,
                            action=EXCLUDED.action,
                            payload=EXCLUDED.payload,
                            created_at=EXCLUDED.created_at
                        """,
                        (
                            row["id"],
                            row["transaction_id"],
                            map_foreign_id(user_id_map, row["user_id"]),
                            row["action"],
                            row["payload"],
                            row["created_at"],
                        ),
                    )

                reset_serial_sequences(pg_conn)

            pg_conn.commit()

        print("Migration complete: SQLite data merged into PostgreSQL.")
    finally:
        sqlite_conn.close()


if __name__ == "__main__":
    main()
