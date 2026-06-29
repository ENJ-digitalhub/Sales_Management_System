# cli/cli.py
from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from backend.models.models import Base, Product, User
from backend.utils.security import Security

base = Path(__file__).parent.parent.resolve()
DB_PATH = base / "database" / "shop.db"  # build an absolute path to database/shop.db using Path(__file__)

engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(bind=engine)

# print(DB_PATH)
class CLI:
    def __init__(self) -> None:
        pass

    def setup(self):
        """Creates all tables in the database. Should be run once during initial setup."""
        Base.metadata.create_all(engine)
        pass

    def reset(self):
        """Deletes all tables and recreates them. Use with caution as this will erase all data."""
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        pass

    def seed(self):
        """Seeds the database with initial data for testing and development purposes."""
        try:
            with SessionLocal() as session:
                # Idempotency check: no duplicate
                product_existing = session.execute(select(Product)).first()
                user_existing = session.execute(select(User)).first()
                
                if product_existing or user_existing:
                    print("Already seeded. Skipping.")
                    return
                
                # Create & Add products
                product1 = Product(name="Rice", category=None, selling_price=999.99, cost_price=999.99, stock_quantity=999)
                product2 = Product(name="Vegetable Oil", category=None, selling_price=999.99, cost_price=999.99, stock_quantity=999)
                product3 = Product(name="Sugar", category=None, selling_price=999.99, cost_price=999.99, stock_quantity=999)
                product4 = Product(name="Flour", category=None, selling_price=999.99, cost_price=999.99, stock_quantity=999)
                product5 = Product(name="Tomato Paste", category=None, selling_price=999.99, cost_price=999.99, stock_quantity=999)

                # Create & Add Users
                user1 = User(name="John", username= "john", password_hash=Security.hash_password("1234567890"), role= "admin", phone_or_email = "john@gmail.com", is_active = True)
                user2 = User(name="Doe", username= "doe", password_hash=Security.hash_password("1234567890"), role= "manager", phone_or_email = "doe@gmail.com", is_active = True)
                user3 = User(name="Jane", username= "jane", password_hash=Security.hash_password("1234567890"), role= "employee", phone_or_email = "jane@gmail.com", is_active = True)

                session.add_all([product1, product2, product3, product4, product5])
                session.add_all([user1, user2, user3])

                # Commit Changes
                session.commit()

                # Querying data
                # Get all product
                all_product = session.execute(select(Product)).scalars().all()
                print(F"All Products: {all_product}")
                
                # Get all user
                all_user = session.execute(select(User)).scalars().all()
                print(F"All Users: {all_user}")


        except Exception as e:
            print(f"Error: {e}")
        pass

if __name__ == "__main__":
    import sys
    cli = CLI()
    command = sys.argv[1]  # Accepts "setup", "seed", or "reset" added behind lunch command
    
    if command == "setup":
        cli.setup()
    elif command == "seed":
        cli.seed()
    elif command == "reset":
        cli.reset()
    else:
        print(f"Unknown command: {command}")