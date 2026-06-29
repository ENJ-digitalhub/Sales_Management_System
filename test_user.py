import uuid
from sqlalchemy import create_engine, text
from backend.utils.security import hash_password

DATABASE_URL = "sqlite:///database/shop.db"
engine = create_engine(DATABASE_URL)

print("🚀 Running schema injection...")

with engine.begin() as connection:
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(60) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'employee',
            phone_or_email VARCHAR(50) NOT NULL,
            account_name VARCHAR(50),
            bank_name VARCHAR(50),
            account_number VARCHAR(10),
            pin_hash VARCHAR(60),
            is_active BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            CHECK (role IN ('admin', 'manager', 'employee'))
        );
    """))
    print("📋 'users' table verified/created.")

    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS devices (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL REFERENCES users(id),
            device_name VARCHAR(20) NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            last_seen_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """))
    print("📋 'devices' table verified/created.")

    try:
        connection.execute(text("DELETE FROM users WHERE username IN ('covenant', 'testemployee');"))

        test_users = [
            {
                "id": str(uuid.uuid4()),
                "name": "Covenant Johnson",
                "username": "covenant",
                "password_hash": hash_password("password123"),
                "role": "admin",
                "phone_or_email": "covenant@kave.dev",
                "is_active": True,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Test Employee",
                "username": "testemployee",
                "password_hash": hash_password("password123"),
                "role": "employee",
                "phone_or_email": "testemployee@kave.dev",
                "is_active": True,
            }
        ]

        for u in test_users:
            connection.execute(
                text("""
                    INSERT INTO users (id, name, username, password_hash, role, phone_or_email, is_active)
                    VALUES (:id, :name, :username, :password_hash, :role, :phone_or_email, :is_active);
                """),
                u
            )
        print(f"✅ Success! {len(test_users)} test accounts ready (covenant/admin, testemployee/employee), password 'password123' for both.")

    except Exception as e:
        print(f"❌ Account injection failed: {e}")