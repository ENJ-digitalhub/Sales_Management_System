# cli/cli.py
from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from backend.models.models import Base, Product, User, Sale, SalesItem, InventoryLogs, AuditLogs, Purchase, PurchaseItem
from backend.utils.security import Security
from datetime import datetime, timedelta

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
                session.flush()
                
                # --- Sales: spread across 3 months so daily/monthly/yearly reports have real data ---
                products = [product1, product2, product3, product4, product5]
                employees = [user3, user2, user1]  # jane (employee), doe (manager), john (admin)
                payment_methods = ["cash", "transfer", "pos"]

                now = datetime.utcnow()
                sales_created = []

                for month_offset in range(3):              # this month, last month, month before
                    for day_offset in [1, 5, 12, 20, 27]:   # 5 distinct days per month
                        sale_date = now - timedelta(days=(month_offset * 30) + day_offset)

                        for i, employee in enumerate(employees):
                            product = products[(month_offset + day_offset + i) % len(products)]
                            quantity = (i % 3) + 1
                            unit_price = product.selling_price
                            cost_price = product.cost_price
                            total_price = unit_price * quantity
                            profit = (unit_price - cost_price) * quantity

                            sale = Sale(
                                receipt_number=f"r{len(sales_created)+1:05d}",
                                user_id=employee.id,
                                total_amount=total_price,
                                profit_at_sale=profit,
                                payment_method=payment_methods[i % len(payment_methods)],
                                status="completed",
                                created_at=sale_date,
                                editable_until=sale_date + timedelta(minutes=20),
                            )
                            session.add(sale)
                            session.flush()  # need sale.id before the FK rows below

                            session.add(SalesItem(
                                sale_id=sale.id,
                                product_id=product.id,
                                quantity=quantity,
                                unit_price=unit_price,
                                cost_price_at_sale=cost_price,
                                total_price=total_price,
                            ))

                            session.add(InventoryLogs(
                                product_id=product.id,
                                change_type="sale",
                                quantity_change=-quantity,
                                reference_id=sale.id,
                                created_at=sale_date,
                            ))

                            session.add(AuditLogs(
                                user_id=employee.id,
                                action_type="create_sale",
                                entity_type="sale",
                                entity_id=sale.id,
                                log_metadata=None,
                                created_at=sale_date,
                            ))

                            sales_created.append(sale)

                print(f"Created {len(sales_created)} sales across 3 months.")
                
                # Create & Add Purchase
                purchase1 = Purchase(created_by=user1.id, supplier="john", status="pending", total_cost=999.99)
                purchase2 = Purchase(created_by=user2.id, supplier="jane", status="rejected", total_cost=999.99)
                purchase3 = Purchase(created_by=user3.id, supplier="doe", status="approved", total_cost=999.99, approved_by=user1.id, approved_at=datetime.utcnow())
                
                session.add_all([purchase1, purchase2, purchase3])
                session.flush()
                
                item1 = PurchaseItem(purchase_id=purchase1.id, product_id=product1.id, quantity=10, cost_price=999.99)
                item2 = PurchaseItem(purchase_id=purchase2.id, product_id=product2.id, quantity=5, cost_price=999.99)
                item3 = PurchaseItem(purchase_id=purchase3.id, product_id=product3.id, quantity=20, cost_price=999.99)

                session.add_all([item1, item2, item3])

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