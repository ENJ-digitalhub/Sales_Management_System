from sqlalchemy.orm import Session, joinedload
from backend.models.models import Purchase, PurchaseItem, Product, InventoryLog, AuditLog
from datetime import datetime, timezone
from decimal import Decimal
import uuid

class PurchasesService:
    @staticmethod
    def create_purchase(session: Session, user_id: str, supplier: str, items: list):
        if not items:
            return None, "Purchase items are required"

        purchase = Purchase(
            supplier=supplier,
            created_by=user_id,
            status="pending",
            total_cost=Decimal("0.00"),
            created_at=datetime.now(timezone.utc)
        )
        session.add(purchase)
        session.flush()

        total_cost = Decimal("0.00")
        purchase_items = []
        for item_data in items:
            product_id = item_data.get("product_id")
            quantity = item_data.get("quantity")
            cost_price = item_data.get("cost_price")

            if not product_id or not isinstance(quantity, int) or quantity <= 0:
                return None, "Each item requires a valid product_id and positive quantity"
            if cost_price is None:
                return None, "Each item requires a cost_price"

            product = session.query(Product).filter_by(id=product_id, is_active=True).first()
            if not product:
                return None, f"Product with ID {product_id} not found or inactive"

            total_price = Decimal(str(cost_price)) * quantity
            total_cost += total_price

            purchase_item = PurchaseItem(
                purchase_id=purchase.id,
                product_id=product_id,
                quantity=quantity,
                cost_price=Decimal(str(cost_price))
            )
            purchase_items.append(purchase_item)
            session.add(purchase_item)

        purchase.total_cost = total_cost
        session.add(purchase)

        session.add(AuditLog(
            user_id=user_id,
            action_type="create_purchase",
            entity_type="purchase",
            entity_id=purchase.id,
            log_metadata={"supplier": supplier, "items": [
                {"product_id": item.product_id, "quantity": item.quantity, "cost_price": float(item.cost_price)} for item in purchase_items
            ]},
            created_at=datetime.now(timezone.utc)
        ))

        session.commit()
        return purchase, None

    @staticmethod
    def get_purchase(session: Session, purchase_id: str):
        purchase = session.query(Purchase).options(joinedload(Purchase.items)).filter_by(id=purchase_id).first()
        if not purchase:
            return None, "Purchase not found"
        return purchase, None

    @staticmethod
    def get_purchase_history(session: Session):
        purchases = session.query(Purchase).options(joinedload(Purchase.items)).order_by(Purchase.created_at.desc()).all()
        return purchases, None

    @staticmethod
    def approve_purchase(session: Session, purchase_id: str, admin_id: str):
        purchase = session.query(Purchase).options(joinedload(Purchase.items)).filter_by(id=purchase_id).first()
        if not purchase:
            return None, "Purchase not found"
        if purchase.status != "pending":
            return None, "Only pending purchases can be approved"

        for item in purchase.items:
            product = session.query(Product).filter_by(id=item.product_id).first()
            if not product or not product.is_active:
                return None, f"Product with ID {item.product_id} not found or inactive"
            product.stock_quantity += item.quantity
            session.add(product)
            session.add(InventoryLog(
                product_id=product.id,
                change_type="restock",
                quantity_change=item.quantity,
                reference_id=purchase.id,
                created_at=datetime.now(timezone.utc)
            ))

        purchase.status = "approved"
        purchase.approved_by = admin_id
        purchase.approved_at = datetime.now(timezone.utc)
        session.add(purchase)

        session.add(AuditLog(
            user_id=admin_id,
            action_type="approve_purchase",
            entity_type="purchase",
            entity_id=purchase.id,
            log_metadata={"approved_by": admin_id, "items": [
                {"product_id": item.product_id, "quantity": item.quantity, "cost_price": float(item.cost_price)} for item in purchase.items
            ]},
            created_at=datetime.now(timezone.utc)
        ))

        session.commit()
        return purchase, None
