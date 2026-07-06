
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from backend.models.models import Sale, SaleItem, Product, InventoryLog, AuditLog, User
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid

class SalesService:
    @staticmethod
    def create_sale(session: Session, user_id: str, items: list, payment_method: str, commit: bool = True):
        # Validate stock and calculate totals
        total_amount = Decimal("0.00")
        profit_at_sale = Decimal("0.00")
        sale_items_to_add = []
        inventory_logs_to_add = []

        for item_data in items:
            product_id = item_data["product_id"]
            quantity = item_data["quantity"]

            product = session.query(Product).filter_by(id=product_id, is_active=True).first()
            if not product:
                session.rollback()
                return None, f"Product with ID {product_id} not found or inactive."
            if product.stock_quantity < quantity:
                session.rollback()
                return None, f"Insufficient stock for product: {product.name}. Available: {product.stock_quantity}, Requested: {quantity}"

            unit_price = product.selling_price
            cost_price = product.cost_price
            item_total_price = unit_price * quantity
            item_profit = (unit_price - cost_price) * quantity

            total_amount += item_total_price
            profit_at_sale += item_profit

            sale_items_to_add.append(SaleItem(
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                cost_price_at_sale=cost_price,
                total_price=item_total_price
            ))

            # Prepare inventory log for stock deduction
            inventory_logs_to_add.append(InventoryLog(
                product_id=product_id,
                change_type="sale",
                quantity_change=-quantity,
                reference_id=None # Will be updated after sale is created
            ))
            # Deduct stock immediately (within the transaction)
            product.stock_quantity -= quantity
            session.add(product)

        # Create sale
        sale = Sale(
            receipt_number=f"REC-{uuid.uuid4().hex[:8].upper()}",
            user_id=user_id,
            total_amount=total_amount,
            profit_at_sale=profit_at_sale,
            payment_method=payment_method,
            status="completed",
            created_at=datetime.now(timezone.utc),
            editable_until=datetime.now(timezone.utc) + timedelta(minutes=20)
        )
        session.add(sale)
        session.flush() # Flush to get sale.id

        # Link sale items and inventory logs to the new sale
        for item in sale_items_to_add:
            item.sale_id = sale.id
            session.add(item)
        for log in inventory_logs_to_add:
            log.reference_id = sale.id
            session.add(log)

        # Add audit log
        session.add(AuditLog(
            user_id=user_id,
            action_type="create_sale",
            entity_type="sale",
            entity_id=sale.id,
            log_metadata={"items": [item.to_dict() for item in sale_items_to_add]},
            created_at=datetime.now(timezone.utc)
        ))

        if commit:
            session.commit()
        return sale, None

    @staticmethod
    def get_sale(session: Session, sale_id: str):
        sale = session.query(Sale).options(joinedload(Sale.items).joinedload(SaleItem.product)).filter_by(id=sale_id).first()
        if not sale:
            return None, "Sale not found"
        return sale, None

    @staticmethod
    def get_all_sales(session: Session):
        sales = session.query(Sale).options(joinedload(Sale.items).joinedload(SaleItem.product)).all()
        return sales, None

    @staticmethod
    def edit_sale(session: Session, sale_id: str, user_id: str, role: str, items: list, payment_method: str):
        sale = session.query(Sale).options(joinedload(Sale.items)).filter_by(id=sale_id).first()
        if not sale:
            return None, "Sale not found"

        # Check edit window for employees
        if role == "employee" and datetime.now(timezone.utc) > sale.editable_until:
            return None, "Edit window has closed. Manager approval required."

        # Revert old stock
        for old_item in sale.items:
            product = session.query(Product).filter_by(id=old_item.product_id).first()
            if product:
                product.stock_quantity += old_item.quantity
                session.add(product)
                session.add(InventoryLog(
                    product_id=product.id,
                    change_type="cancellation",
                    quantity_change=old_item.quantity,
                    reference_id=sale.id,
                    created_at=datetime.now(timezone.utc)
                ))
        
        # Clear old sale items
        session.query(SaleItem).filter_by(sale_id=sale.id).delete()
        session.flush()

        # Process new items (similar to create_sale)
        total_amount = Decimal("0.00")
        profit_at_sale = Decimal("0.00")
        new_sale_items = []
        new_inventory_logs = []

        for item_data in items:
            product_id = item_data["product_id"]
            quantity = item_data["quantity"]

            product = session.query(Product).filter_by(id=product_id, is_active=True).first()
            if not product:
                session.rollback()
                return None, f"Product with ID {product_id} not found or inactive."
            if product.stock_quantity < quantity:
                session.rollback()
                return None, f"Insufficient stock for product: {product.name}. Available: {product.stock_quantity}, Requested: {quantity}"

            unit_price = product.selling_price
            cost_price = product.cost_price
            item_total_price = unit_price * quantity
            item_profit = (unit_price - cost_price) * quantity

            total_amount += item_total_price
            profit_at_sale += item_profit

            new_sale_items.append(SaleItem(
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                cost_price_at_sale=cost_price,
                total_price=item_total_price,
                sale_id=sale.id
            ))

            new_inventory_logs.append(InventoryLog(
                product_id=product_id,
                change_type="sale",
                quantity_change=-quantity,
                reference_id=sale.id,
                created_at=datetime.now(timezone.utc)
            ))
            product.stock_quantity -= quantity
            session.add(product)

        sale.total_amount = total_amount
        sale.profit_at_sale = profit_at_sale
        sale.payment_method = payment_method
        sale.status = "edited"
        sale.editable_until = datetime.now(timezone.utc) + timedelta(minutes=20) # Reset edit window

        session.add_all(new_sale_items)
        session.add_all(new_inventory_logs)
        session.add(sale)

        session.add(AuditLog(
            user_id=user_id,
            action_type="edit_sale",
            entity_type="sale",
            entity_id=sale.id,
            log_metadata={"old_items": [item.to_dict() for item in sale.items], "new_items": [item.to_dict() for item in new_sale_items]},
            created_at=datetime.now(timezone.utc)
        ))

        session.commit()
        return sale, None

    @staticmethod
    def cancel_sale(session: Session, sale_id: str, user_id: str, role: str):
        sale = session.query(Sale).options(joinedload(Sale.items)).filter_by(id=sale_id).first()
        if not sale:
            return None, "Sale not found"

        if sale.status == "cancelled":
            return None, "Sale is already cancelled"

        # Only managers and admins can cancel
        if role not in ["admin", "manager"]:
            return None, "Permission denied: Only managers or admins can cancel sales."

        # Restore stock
        for item in sale.items:
            product = session.query(Product).filter_by(id=item.product_id).first()
            if product:
                product.stock_quantity += item.quantity
                session.add(product)
                session.add(InventoryLog(
                    product_id=product.id,
                    change_type="cancellation",
                    quantity_change=item.quantity,
                    reference_id=sale.id,
                    created_at=datetime.now(timezone.utc)
                ))

        sale.status = "cancelled"
        session.add(sale)

        session.add(AuditLog(
            user_id=user_id,
            action_type="cancel_sale",
            entity_type="sale",
            entity_id=sale.id,
            log_metadata={"reason": "Cancelled by user"},
            created_at=datetime.now(timezone.utc)
        ))

        session.commit()
        return sale, None

    @staticmethod
    def delete_sale(session: Session, sale_id: str, user_id: str):
        sale = session.query(Sale).filter_by(id=sale_id).first()
        if not sale:
            return None, "Sale not found"

        session.add(AuditLog(
            user_id=user_id,
            action_type="delete_sale",
            entity_type="sale",
            entity_id=sale.id,
            log_metadata={"reason": "Deleted by admin"},
            created_at=datetime.now(timezone.utc)
        ))

        session.delete(sale)
        session.commit()
        return None, None

    @staticmethod
    def request_edit(session: Session, sale_id: str, user_id: str, role: str, reason: str, proposed_changes: dict):
        sale = session.query(Sale).filter_by(id=sale_id).first()
        if not sale:
            return None, "Sale not found"

        if datetime.now(timezone.utc) <= sale.editable_until:
            return None, "Sale is still within the editable window and does not require a late edit request"

        if role not in ["admin", "manager"]:
            return None, "Permission denied: only managers or admins can request late sale edits"

        session.add(AuditLog(
            user_id=user_id,
            action_type="edit_sale",
            entity_type="sale",
            entity_id=sale.id,
            log_metadata={
                "reason": reason,
                "proposed_changes": proposed_changes,
                "late_edit_request": True
            },
            created_at=datetime.now(timezone.utc)
        ))

        session.commit()
        return sale, None


# Helper for SaleItem to_dict (for audit log metadata)
def to_dict(self):
    return {c.name: getattr(self, c.name) for c in self.__table__.columns}
SaleItem.to_dict = to_dict
