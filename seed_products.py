import os
from sqlalchemy import create_engine, text

os.makedirs("database", exist_ok=True)
DATABASE_URL = "sqlite:///database/shop.db"
engine = create_engine(DATABASE_URL)

print("🚀 Creating products table...")

with engine.begin() as connection:
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku VARCHAR(50) NOT NULL UNIQUE,
            name VARCHAR(150) NOT NULL,
            category VARCHAR(80) NOT NULL,
            cost_price NUMERIC(10, 2) NOT NULL,
            selling_price NUMERIC(10, 2) NOT NULL,
            stock_quantity INTEGER NOT NULL DEFAULT 0,
            is_active BOOLEAN DEFAULT 1
        );
    """))
    print("📋 'products' table verified/created successfully.")

    try:
        connection.execute(text("DELETE FROM products WHERE sku IN ('SKU-001', 'SKU-002', 'SKU-003');"))

        sample_products = [
            {"sku": "SKU-001", "name": "Bag of Rice (50kg)", "category": "Grains", "cost_price": 32000.00, "selling_price": 38000.00, "stock_quantity": 42, "is_active": True},
            {"sku": "SKU-002", "name": "Cooking Oil 5L", "category": "Cooking", "cost_price": 9500.00, "selling_price": 11500.00, "stock_quantity": 17, "is_active": True},
            {"sku": "SKU-003", "name": "Detergent 1kg", "category": "Household", "cost_price": 1200.00, "selling_price": 1800.00, "stock_quantity": 4, "is_active": True},
        ]

        for p in sample_products:
            connection.execute(
                text("""
                    INSERT INTO products (sku, name, category, cost_price, selling_price, stock_quantity, is_active)
                    VALUES (:sku, :name, :category, :cost_price, :selling_price, :stock_quantity, :is_active);
                """),
                p
            )
        print(f"✅ Success! {len(sample_products)} sample products seeded.")

    except Exception as e:
        print(f"❌ Product seeding failed: {e}")