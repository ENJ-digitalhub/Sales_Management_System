import os
from sqlalchemy import create_engine, text
from backend.utils.security import hash_password

os.makedirs("database", exist_ok=True)
DATABASE_URL = "sqlite:///database/shop.db"
engine = create_engine(DATABASE_URL)

print("🚀 Running schema injection...")

with engine.begin() as connection:
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL,
            phone_or_email VARCHAR(150),
            account_name VARCHAR(150),
            bank_name VARCHAR(100),
            account_number VARCHAR(50),
            pin_hash VARCHAR(255),
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """))
    print("📋 'users' table verified/created.")

    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            device_name VARCHAR(150) NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            last_seen_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """))
    print("📋 'devices' table verified/created.")

    try:
        connection.execute(text("DELETE FROM users WHERE username IN ('covenant', 'testemployee');"))

        test_users = [
            {
                "name": "Covenant Johnson",
                "username": "covenant",
                "password_hash": hash_password("password123"),
                "role": "admin",
            },
            {
                "name": "Test Employee",
                "username": "testemployee",
                "password_hash": hash_password("password123"),
                "role": "employee",
            }
        ]

        for u in test_users:
            connection.execute(
                text("""
                    INSERT INTO users (name, username, password_hash, role)
                    VALUES (:name, :username, :password_hash, :role);
                """),
                u
            )
        print(f"✅ Success! {len(test_users)} test accounts ready (covenant/admin, testemployee/employee), password 'password123' for both.")

    except Exception as e:
        print(f"❌ Account injection failed: {e}")