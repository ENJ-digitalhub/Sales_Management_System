import os
from sqlalchemy import create_engine, text
from backend.utils.security import hash_password

# 1. Ensure the instance directory exists and link to SQLite file
os.makedirs("instance", exist_ok=True)
DATABASE_URL = "sqlite:///instance/sms.db"
engine = create_engine(DATABASE_URL)

print("🚀 Running pure schema injection...")

with engine.begin() as connection:
    # 2. Build ONLY the users table manually
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL,
            is_active BOOLEAN DEFAULT 1
        );
    """))
    print("📋 Pure SQL: 'users' table verified/created successfully.")

    # 3. Clean up any leftover records and insert the testing administrator account
    try:
        connection.execute(text("DELETE FROM users WHERE username = 'covenant';"))
        
        connection.execute(
            text("""
                INSERT INTO users (username, password_hash, role, is_active)
                VALUES (:username, :password_hash, :role, :is_active);
            """),
            {
                "username": "covenant",
                "password_hash": hash_password("password123"),
                "role": "admin",
                "is_active": True
            }
        )
        print("✅ Success! Test account 'covenant' with password 'password123' is ready.")
        
    except Exception as e:
        print(f"❌ Account injection failed: {e}")