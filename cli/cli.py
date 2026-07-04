import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# cli/cli.py
import uuid
from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from backend.models.models import Base, Product, User, Sale, Purchase, PurchaseItem
from backend.utils.security import Security
from datetime import datetime, timedelta, timezone

base = Path(__file__).parent.parent.resolve()
INSTANCE_DIR = base / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = (INSTANCE_DIR / "shop.db").resolve()  # now matches Config.SQLALCHEMY_DATABASE_URI

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
                product1 = Product(name="Rice", sku="SKU-RICE-001", category="Grains", selling_price=999.99, cost_price=999.99, stock_quantity=999)
                product2 = Product(name="Vegetable Oil", sku="SKU-OIL-002", category="Oil", selling_price=999.99, cost_price=999.99, stock_quantity=999)
                product3 = Product(name="Sugar", sku="SKU-SUG-003", category="Sweeteners", selling_price=999.99, cost_price=999.99, stock_quantity=999)
                product4 = Product(name="Flour", sku="SKU-FLR-004", category="Grains", selling_price=999.99, cost_price=999.99, stock_quantity=999)
                product5 = Product(name="Tomato Paste", sku="SKU-TOM-005", category="Canned Goods", selling_price=999.99, cost_price=999.99, stock_quantity=999)

                # Create & Add Users
                user1 = User(name="John", username="john", password_hash=Security.hash_password("1234567890"), role="admin", phone_or_email="john@gmail.com", is_active=1)
                user2 = User(name="Doe", username="doe", password_hash=Security.hash_password("1234567890"), role="manager", phone_or_email="doe@gmail.com", is_active=1)
                user3 = User(name="Jane", username="jane", password_hash=Security.hash_password("1234567890"), role="employee", phone_or_email="jane@gmail.com", is_active=1)

                session.add_all([product1, product2, product3, product4, product5])
                session.add_all([user1, user2, user3])
                session.flush()
                
                # Dynamic timestamp boundary for editable_until constraint
                future_time = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)

                # Demo device ids — one per user, simulating each seeded user
                # having logged in from a single device. Sale.device_id has
                # no FK constraint, so any unique string is valid here.
                device_john = str(uuid.uuid4())
                device_doe = str(uuid.uuid4())
                device_jane = str(uuid.uuid4())

                # Create & Add Sales
                # client_transaction_id must be unique per sale (UniqueConstraint on Sale)
                # payment_method values must match ALLOWED_PAYMENT_METHODS in validators.py
                sale1 = Sale(client_transaction_id=str(uuid.uuid4()), device_id=device_john, receipt_number="r0001", user_id=user1.id, total_amount=999.99, profit_at_sale=99.99, payment_method="cash", status="completed", editable_until=future_time)
                sale2 = Sale(client_transaction_id=str(uuid.uuid4()), device_id=device_doe, receipt_number="r0002", user_id=user2.id, total_amount=999.99, profit_at_sale=99.99, payment_method="bank_transfer", payment_provider="gtbank", status="edited", editable_until=future_time)
                sale3 = Sale(client_transaction_id=str(uuid.uuid4()), device_id=device_jane, receipt_number="r0003", user_id=user3.id, total_amount=999.99, profit_at_sale=99.99, payment_method="bank_transfer", payment_provider="zenith", status="cancelled", editable_until=future_time)
                sale4 = Sale(client_transaction_id=str(uuid.uuid4()), device_id=device_john, receipt_number="r0004", user_id=user1.id, total_amount=999.99, profit_at_sale=99.99, payment_method="pos_terminal", payment_provider="moniepoint", status="cancelled", editable_until=future_time)
                sale5 = Sale(client_transaction_id=str(uuid.uuid4()), device_id=device_doe, receipt_number="r0005", user_id=user2.id, total_amount=999.99, profit_at_sale=99.99, payment_method="cash", status="edited", editable_until=future_time)
                
                session.add_all([sale1, sale2, sale3, sale4, sale5])
                
                # Create & Add Purchase
                purchase1 = Purchase(created_by=user1.id, supplier="john", status="pending", total_cost=999.99)
                purchase2 = Purchase(created_by=user2.id, supplier="jane", status="rejected", total_cost=999.99)
                purchase3 = Purchase(created_by=user3.id, supplier="doe", status="approved", total_cost=999.99, approved_by=user1.id, approved_at=datetime.now(timezone.utc).replace(tzinfo=None))
                
                session.add_all([purchase1, purchase2, purchase3])
                session.flush()
                
                # Added explicit unit_cost and line_total parameters to pass constraints
                item1 = PurchaseItem(purchase_id=purchase1.id, product_id=product1.id, quantity=10, unit_cost=999.99, line_total=9999.90)
                item2 = PurchaseItem(purchase_id=purchase2.id, product_id=product2.id, quantity=5, unit_cost=999.99, line_total=4999.95)
                item3 = PurchaseItem(purchase_id=purchase3.id, product_id=product3.id, quantity=20, unit_cost=999.99, line_total=19999.80)

                session.add_all([item1, item2, item3])

                # Commit Changes
                session.commit()

                # Querying data
                # Get all product
                all_product = session.execute(select(Product)).scalars().all()
                print(f"All Products: {all_product}")
                
                # Get all user
                all_user = session.execute(select(User)).scalars().all()
                print(f"All Users: {all_user}")


        except Exception as e:
            print(f"Error: {e}")
        pass

if __name__ == "__main__":
    cli = CLI()

    if len(sys.argv) < 2:
        print("Usage: python cli/cli.py [setup|seed|reset]")
        sys.exit(1)

    command = sys.argv[1]  # Accepts "setup", "seed", or "reset"

    if command == "setup":
        cli.setup()
    elif command == "seed":
        cli.seed()
    elif command == "reset":
        cli.reset()
    else:
        print(f"Unknown command: {command}")