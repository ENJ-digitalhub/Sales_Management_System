from backend.database import SessionLocal
from backend.models.models import Product

def seed_inventory():
    print("Connecting to storage engine to populate product rows...")
    
    with SessionLocal() as session:
        # Check if products already exist to avoid duplication crashes
        existing_count = session.query(Product).count()
        if existing_count > 0:
            print(f"Inventory already populated with {existing_count} items. Skipping mock seeder.")
            return

        mock_items = [
            Product(name="Wireless Mouse", description="Ergonomic 2.4GHz wireless mouse", price=25.50, stock_quantity=120),
            Product(name="Mechanical Keyboard", description="RGB backlit clicky mechanical switches", price=79.99, stock_quantity=45),
            Product(name="Type-C USB Hub", description="5-in-1 multi-port adapter with HDMI out", price=34.95, stock_quantity=60)
        ]

        session.add_all(mock_items)
        session.commit()
        print("🎉 Success! Added 3 default testing products to your inventory schema.")

if __name__ == "__main__":
    seed_inventory()