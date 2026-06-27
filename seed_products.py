import uuid
from sqlalchemy import create_engine, text

DATABASE_URL = "sqlite:///database/shop.db"
engine = create_engine(DATABASE_URL)

print("🚀 Creating products table...")

with engine.begin() as connection:
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS products (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            category VARCHAR(100),
            selling_price NUMERIC(10, 2) NOT NULL,
            cost_price NUMERIC(10, 2) NOT NULL,
            stock_quantity INTEGER NOT NULL DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """))
    print("📋 'products' table verified/created successfully.")

    sample_products = [
        {"id": str(uuid.uuid4()), "name": "Bag of Rice (50kg)", "category": "Grains", "cost_price": 32000.00, "selling_price": 38000.00, "stock_quantity": 42},
        {"id": str(uuid.uuid4()), "name": "Cooking Oil 5L", "category": "Cooking", "cost_price": 9500.00, "selling_price": 11500.00, "stock_quantity": 17},
        {"id": str(uuid.uuid4()), "name": "Detergent 1kg", "category": "Household", "cost_price": 1200.00, "selling_price": 1800.00, "stock_quantity": 4},
    ]

    for p in sample_products:
        connection.execute(
            text("""
                INSERT INTO products (id, name, category, cost_price, selling_price, stock_quantity)
                VALUES (:id, :name, :category, :cost_price, :selling_price, :stock_quantity);
            """),
            p
        )
    print(f"✅ Success! {len(sample_products)} sample products seeded.")