import os
from sqlalchemy import create_engine, text
from backend.utils.security import hash_password

os.makedirs("database", exist_ok=True)
DATABASE_URL = "sqlite:///database/shop.db"
engine = create_engine(DATABASE_URL)

print("🚀 Running pure schema injection...")

with engine.begin() as connection:
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL,
            is_active BOOLEAN DEFAULT 1
        );
    """))
    print("📋 Pure SQL: 'users' table verified/created successfully.")

    try:
        connection.execute(text("DELETE FROM users WHERE username = 'covenant';"))

        connection.execute(
            text("""
                INSERT INTO users (name, username, password_hash, role, is_active)
                VALUES (:name, :username, :password_hash, :role, :is_active);
            """),
            {
                "name": "Covenant Johnson",
                "username": "covenant",
                "password_hash": hash_password("password123"),
                "role": "admin",
                "is_active": True
            }
        )
        print("✅ Success! Test account 'covenant' with password 'password123' is ready.")

    except Exception as e:
        print(f"❌ Account injection failed: {e}")
        import os
from sqlalchemy import create_engine, text
from backend.utils.security import hash_password

os.makedirs("database", exist_ok=True)
DATABASE_URL = "sqlite:///database/shop.db"
engine = create_engine(DATABASE_URL)

print("🚀 Running pure schema injection...")

with engine.begin() as connection:
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL,
            is_active BOOLEAN DEFAULT 1
        );
    """))
    print("📋 Pure SQL: 'users' table verified/created successfully.")

    try:
        connection.execute(text("DELETE FROM users WHERE username IN ('covenant', 'testemployee');"))

        test_users = [
            {
                "name": "Covenant Johnson",
                "username": "covenant",
                "password_hash": hash_password("password123"),
                "role": "admin",
                "is_active": True
            },
            {
                "name": "Test Employee",
                "username": "testemployee",
                "password_hash": hash_password("password123"),
                "role": "employee",
                "is_active": True
            }
        ]

        for u in test_users:
            connection.execute(
                text("""
                    INSERT INTO users (name, username, password_hash, role, is_active)
                    VALUES (:name, :username, :password_hash, :role, :is_active);
                """),
                u
            )
        print(f"✅ Success! {len(test_users)} test accounts ready (covenant/admin, testemployee/employee), password 'password123' for both.")

    except Exception as e:
        print(f"❌ Account injection failed: {e}")