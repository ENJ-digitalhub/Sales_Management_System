# cli/cli.py
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.models import Base, Product

base = Path(__file__).parent.parent.resolve()
DB_PATH = base / "database" / "shop.db"  # build an absolute path to database/shop.db using Path(__file__)

engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(bind=engine)

# print(DB_PATH)
class CLI:
    def __init__(self) -> None:
        pass

    """Creates all tables in the database. Should be run once during initial setup."""
    def setup(self):
        Base.metadata.create_all(engine)
        pass

    """Deletes all tables and recreates them. Use with caution as this will erase all data."""
    def reset(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        pass

    """Seeds the database with initial data for testing and development purposes."""
    def seed(self):
        try:
            with SessionLocal() as session:
                # Create & Add User
                product1 = Product(id="P01", name="John Doe", category=None, selling_price=999.99, cost_price=999.99, stock_quantity=999)
                product2 = Product(id="P02", name="Jane Doe", category=None, selling_price=999.99, cost_price=999.99, stock_quantity=999)
                product3 = Product(id="P03", name="John Smith", category=None, selling_price=999.99, cost_price=999.99, stock_quantity=999)
                product4 = Product(id="P04", name="Jane Smith", category=None, selling_price=999.99, cost_price=999.99, stock_quantity=999)
                product5 = Product(id="P05", name="John Appleseed", category=None, selling_price=999.99, cost_price=999.99, stock_quantity=999)


                session.add_all([product1, product2, product3, product4, product5])

                # Commit Changes
                session.commit()

                # Querying data
                # Get all product
                all_product = session.query(Product).all()
                print(F"All Products: {all_product}")

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