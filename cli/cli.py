# cli\cli.py
from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from backend.models.models import Base, Item, User, Sale, SaleItem, InventoryLog, AuditLog, Purchase, PurchaseItem, Device, SyncQueue
from backend.utils.security import Security
from datetime import datetime, timedelta, UTC
from decimal import Decimal
import uuid
from backend.database import engine, SessionLocal

base = Path(__file__).parent.parent.resolve()
DB_PATH = base / "database" / "shop.db"

class CLI:
    def __init__(self) -> None:
        pass

    def setup(self):
        """Creates all tables in the database. Should be run once during initial setup."""
        Base.metadata.create_all(engine)
        print("Database tables created.")

    def reset(self):
        """Deletes all tables and recreates them. Use with caution as this will erase all data."""
        # Drop tables in reverse order of dependency to avoid foreign key constraints issues
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        print("Database tables reset.")

    def seed(self):
        """Seeds the database with initial data for testing and development purposes."""
        try:
            with SessionLocal() as session:
                # Idempotency check: no duplicate
                item_existing = session.execute(select(Item)).first()
                user_existing = session.execute(select(User)).first()
                
                if item_existing or user_existing:
                    print("Already seeded. Skipping.")
                    return
                
                # Create & Add items
                item1 = Item(name="Rice", selling_price=15.00, cost_price=10.00, stock_quantity=100)
                item2 = Item(name="Vegetable Oil", selling_price=25.50, cost_price=18.00, stock_quantity=50)
                item3 = Item(name="Sugar", selling_price=8.75, cost_price=5.50, stock_quantity=200)
                item4 = Item(name="Printing",type="service", selling_price=12.20, cost_price=8.00)
                item5 = Item(name="Photocopy",type="service", selling_price=6.90, cost_price=4.00)

                session.add_all([item1, item2, item3, item4, item5])
                session.flush()
                
                # Create & Add Users
                user_admin = User(name="John Admin", username="admin", password_hash=Security.hash_password("password"), role="admin", phone_or_email="admin@example.com")
                user_manager = User(name="Jane Manager", username="manager", password_hash=Security.hash_password("password"), role="manager", phone_or_email="manager@example.com")
                user_employee = User(name="Peter Employee", username="employee", password_hash=Security.hash_password("password"), role="employee", phone_or_email="employee@example.com")

                session.add_all([user_admin, user_manager, user_employee])
                session.flush()

                # Create & Add Devices
                device_admin_pc = Device(user_id=user_admin.id, device_name="Admin PC")
                device_manager_tablet = Device(user_id=user_manager.id, device_name="Manager Tablet")
                device_employee_mobile = Device(user_id=user_employee.id, device_name="Employee Mobile")

                session.add_all([device_admin_pc, device_manager_tablet, device_employee_mobile])
                session.flush()

                # --- Sales: spread across 3 months so daily/monthly/yearly reports have real data ---
                items_list = [item1, item2, item3, item4, item5]
                employees_list = [user_employee, user_manager, user_admin]  # employee, manager, admin
                payment_methods = ["cash", "transfer", "pos"]

                now = datetime.now(UTC)
                sales_created = []

                for month_offset in range(3):              # this month, last month, month before
                    for day_offset in [1, 5, 12, 20, 27]:   # 5 distinct days per month
                        sale_date = now - timedelta(days=(month_offset * 30) + day_offset)

                        for i, employee in enumerate(employees_list):
                            item = items_list[(month_offset + day_offset + i) % len(items_list)]
                            quantity = (i % 3) + 1
                            unit_price = item.selling_price
                            cost_price = item.cost_price
                            total_price = unit_price * quantity
                            profit = (unit_price - cost_price) * quantity

                            sale = Sale(
                                receipt_number=f"REC-{len(sales_created)+1:05d}",
                                user_id=employee.id,
                                total_amount=total_price,
                                profit_at_sale=profit,
                                payment_method=payment_methods[i % len(payment_methods)],
                                status="completed",
                                created_at=sale_date,
                            )
                            session.add(sale)
                            session.flush()  # need sale.id before the FK rows below

                            session.add(SaleItem(
                                sale_id=sale.id,
                                item_id=item.id,
                                quantity=quantity,
                                unit_price=unit_price,
                                cost_price_at_sale=cost_price,
                                total_price=total_price,
                            ))

                            session.add(InventoryLog(
                                item_id=item.id,
                                change_type="sale",
                                quantity_change=-quantity,
                                reference_id=sale.id,
                                created_at=sale_date,
                            ))

                            session.add(AuditLog(
                                user_id=employee.id,
                                action_type="create_sale",
                                entity_type="sale",
                                entity_id=sale.id,
                                log_metadata={"items": [{"item_id": item.id, "quantity": quantity}]}
,                                created_at=sale_date,
                            ))

                            sales_created.append(sale)

                print(f"Created {len(sales_created)} sales across 3 months.")
                
                # Create & Add Purchases
                purchase1 = Purchase(created_by=user_manager.id, supplier="Supplier A", status="pending", total_cost=Decimal("100.00"))
                purchase2 = Purchase(created_by=user_employee.id, supplier="Supplier B", status="rejected", total_cost=Decimal("50.00"))
                purchase3 = Purchase(created_by=user_admin.id, supplier="Supplier C", status="approved", total_cost=Decimal("200.00"), approved_by=user_admin.id, approved_at=datetime.now(UTC))
                
                session.add_all([purchase1, purchase2, purchase3])
                session.flush()
                
                item1 = PurchaseItem(purchase_id=purchase1.id, item_id=item1.id, quantity=10, cost_price=Decimal("7.50"))
                item2 = PurchaseItem(purchase_id=purchase2.id, item_id=item2.id, quantity=5, cost_price=Decimal("12.00"))
                item3 = PurchaseItem(purchase_id=purchase3.id, item_id=item3.id, quantity=20, cost_price=Decimal("4.00"))

                session.add_all([item1, item2, item3])
                session.flush()

                # Add InventoryLog for approved purchase
                session.add(InventoryLog(
                    item_id=item3.id,
                    change_type="restock",
                    quantity_change=20,
                    reference_id=purchase3.id,
                    created_at=datetime.now(UTC),
                ))

                print(f"Created 3 purchases.")

                session.commit()
                print("Database seeded successfully.")

        except Exception as e:
            session.rollback()
            print(f"Error seeding database: {e}")


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
