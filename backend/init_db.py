import uuid
from backend.database import Base, engine, SessionLocal
from backend.models.product import Product

def init_database():
    Base.metadata.drop_all(bind=engine)  # Fresh start
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Seed test data
        test_products = [
            Product(id=str(uuid.uuid4()), sku="PROD-001", name="Wireless Mouse", price=25.50, stock_quantity=100),
            Product(id=str(uuid.uuid4()), sku="PROD-002", name="Mechanical Keyboard", price=89.99, stock_quantity=45),
        ]
        db.add_all(test_products)
        db.commit()
        print("Database initialized & seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        SessionLocal.remove()

if __name__ == "__main__":
    init_database()