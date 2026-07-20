
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from backend.models.models import Sale, SaleItem, Item, InventoryLog, AuditLog, User
from datetime import datetime, timedelta
from backend.utils.time import now_utc
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
            item_id = item_data["item_id"]
            quantity = item_data["quantity"]

            item = session.query(Item).filter_by(id=item_id, is_active=True).first()
            if not item:
                session.rollback()
                return None, f"Item with ID {item_id} not found or inactive."
            if item.stock_quantity < quantity:
                session.rollback()
                return None, f"Insufficient stock for Item: {item.name}. Available: {item.stock_quantity}, Requested: {quantity}"


            unit_price = item.selling_price
            cost_price = item.cost_price
            item_total_price = unit_price * quantity
            item_profit = (unit_price - cost_price) * quantity

            total_amount += item_total_price
            profit_at_sale += item_profit

            sale_items_to_add.append(SaleItem(
                item_id=item_id,
                quantity=quantity,
                unit_price=unit_price,
                cost_price_at_sale=cost_price,
                total_price=item_total_price
            ))

            # Prepare inventory log for stock deduction
            inventory_logs_to_add.append(InventoryLog(
                item_id=item_id,
                change_type="sale",
                quantity_change=-quantity,
                reference_id=None # Will be updated after sale is created
            ))
            # Deduct stock immediately (within the transaction)
            item.stock_quantity -= quantity
            session.add(item)

        # Create sale
        sale = Sale(
            receipt_number=f"REC-{uuid.uuid4().hex[:8].upper()}",
            user_id=user_id,
            total_amount=total_amount,
            profit_at_sale=profit_at_sale,
            payment_method=payment_method,
            status="completed",
            created_at=now_utc()
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
            created_at=now_utc()
        ))

        if commit:
            session.commit()
        return sale, None

    @staticmethod
    def get_sale(session: Session, sale_id: str):
        sale = session.query(Sale).options(joinedload(Sale.items).joinedload(SaleItem.item)).filter_by(id=sale_id).first()
        if not sale:
            return None, "Sale not found"
        return sale, None

    @staticmethod
    def get_all_sales(session: Session, user_id: str = None, role: str = None):
        query = session.query(Sale).options(joinedload(Sale.items).joinedload(SaleItem.item))
        if role == "employee":
            query = query.filter(Sale.user_id == user_id)
        return query.all(), None

    @staticmethod
    def edit_sale(session: Session, sale_id: str, user_id: str, role: str, items: list, payment_method: str):
        sale = session.query(Sale).options(joinedload(Sale.items)).filter_by(id=sale_id).first()
        if not sale:
            return None, "Sale not found"

        # Check edit window for employees
        if role == "employee" and now_utc() > sale.editable_until:
            return None, "Edit window has closed. Manager approval required."

        # Revert old stock
        for old_item in sale.items:
            item = session.query(Item).filter_by(id=old_item.item_id).first()
            if item:
                item.stock_quantity += old_item.quantity
                session.add(item)
                session.add(InventoryLog(
                    item_id=item.id,
                    change_type="cancellation",
                    quantity_change=old_item.quantity,
                    reference_id=sale.id,
                    created_at=now_utc()
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
            item_id = item_data["item_id"]
            quantity = item_data["quantity"]

            item = session.query(Item).filter_by(id=item_id, is_active=True).first()
            if not item:
                session.rollback()
                return None, f"item with ID {item_id} not found or inactive."
            if item.stock_quantity < quantity:
                session.rollback()
                return None, f"Insufficient stock for item: {item.name}. Available: {item.stock_quantity}, Requested: {quantity}"

            unit_price = item.selling_price
            cost_price = item.cost_price
            item_total_price = unit_price * quantity
            item_profit = (unit_price - cost_price) * quantity

            total_amount += item_total_price
            profit_at_sale += item_profit

            new_sale_items.append(SaleItem(
                item_id=item_id,
                quantity=quantity,
                unit_price=unit_price,
                cost_price_at_sale=cost_price,
                total_price=item_total_price,
                sale_id=sale.id
            ))

            new_inventory_logs.append(InventoryLog(
                item_id=item_id,
                change_type="sale",
                quantity_change=-quantity,
                reference_id=sale.id,
                created_at=now_utc()
            ))
            item.stock_quantity -= quantity
            session.add(item)

        sale.total_amount = total_amount
        sale.profit_at_sale = profit_at_sale
        sale.payment_method = payment_method
        sale.status = "edited"
        sale.editable_until = now_utc() + timedelta(minutes=20) # Reset edit window

        session.add_all(new_sale_items)
        session.add_all(new_inventory_logs)
        session.add(sale)

        session.add(AuditLog(
            user_id=user_id,
            action_type="edit_sale",
            entity_type="sale",
            entity_id=sale.id,
            log_metadata={"items": [item.to_dict() for item in new_sale_items]},
            created_at=now_utc()
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

        # Restore stock
        for sale_item in sale.items:
            product = session.query(Item).filter_by(id=sale_item.item_id).first()
            if product:
                product.stock_quantity += sale_item.quantity
                session.add(product)
                session.add(InventoryLog(
                    item_id=product.id,
                    change_type="cancellation",
                    quantity_change=sale_item.quantity,
                    reference_id=sale.id,
                    created_at=now_utc()
                ))

        sale.status = "cancelled"
        session.add(sale)

        session.add(AuditLog(
            user_id=user_id,
            action_type="cancel_sale",
            entity_type="sale",
            entity_id=sale.id,
            log_metadata={"reason": "Cancelled by user"},
            created_at=now_utc()
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
            created_at=now_utc()
        ))

        session.delete(sale)
        session.commit()
        return None, None

    @staticmethod
    def request_edit(session: Session, sale_id: str, user_id: str, role: str, reason: str, proposed_changes: dict):
        sale = session.query(Sale).filter_by(id=sale_id).first()
        if not sale:
            return None, "Sale not found"

        if now_utc() <= sale.editable_until:
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
            created_at=now_utc()
        ))

        session.commit()
        return sale, None