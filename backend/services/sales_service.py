
<<<<<<< HEAD
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from backend.models.models import Sale, SaleItem, Product, InventoryLog, AuditLog
from backend.utils.validators import VALID_PAYMENT_METHODS


class InsufficientStockError(Exception):
    def __init__(self, product_name: str, product_id: str):
        self.product_name = product_name
        self.product_id = product_id
        super().__init__(f"Insufficient stock for product: {product_name}")


def _generate_receipt_number(session) -> str:
    today = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"RCP-{today}-"
    count = session.execute(
        select(func.count(Sale.id)).where(Sale.receipt_number.like(f"{prefix}%"))
    ).scalar() or 0
    return f"{prefix}{str(count + 1).zfill(4)}"


def _serialize_sale(sale, items) -> dict:
    return {
        "id": sale.id,
        "client_transaction_id": sale.client_transaction_id,
        "device_id": sale.device_id,
        "receipt_number": sale.receipt_number,
        "user_id": sale.user_id,
        "total_amount": float(sale.total_amount),
        "profit_at_sale": float(sale.profit_at_sale),
        "payment_method": sale.payment_method,


        "status": sale.status,
        "created_at": sale.created_at.isoformat() if sale.created_at else None,
        "editable_until": sale.editable_until.isoformat() if sale.editable_until else None,
        "items": [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "total_price": float(item.total_price),
            }
            for item in items
        ],
    }


def _create_audit_log(session, user_id: str, action_type: str, entity_type: str, entity_id: str, metadata: dict = None):
    session.add(AuditLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        log_metadata=metadata or {},
        created_at=datetime.utcnow(),
    ))


def _normalize_items(items: list) -> list:
    agg = {}
    for item in items:
        pid = item["product_id"]
        qty = int(item["quantity"])
        if qty <= 0:
            raise ValueError("Quantity must be a positive integer")
        agg[pid] = agg.get(pid, 0) + qty
    return [{"product_id": pid, "quantity": qty} for pid, qty in agg.items()]


def _validate_payment(payment_method: str):
    if payment_method not in VALID_PAYMENT_METHODS:
        raise ValueError("Invalid payment_method")




class SalesService:
    @staticmethod
    def get_paginated_products(session, page: int, per_page: int) -> dict:
        offset = (page - 1) * per_page
        total = session.execute(
            select(func.count(Product.id)).where(Product.is_active == 1)
        ).scalar() or 0
        products = session.execute(
            select(Product).where(Product.is_active == 1).offset(offset).limit(per_page)
        ).scalars().all()
        return {
            "items": [
                {
                    "id": p.id,
                    "name": p.name,
                    "category": p.category,
                    "selling_price": float(p.selling_price),
                    "cost_price": float(p.cost_price),
                    "stock_quantity": p.stock_quantity,
                }
                for p in products
            ],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def update_product(session, product_id: str, updates: dict):
        allowed = {"name", "category", "cost_price", "selling_price", "stock_quantity", "is_active"}
        numeric_non_negative = {"cost_price", "selling_price", "stock_quantity"}

        product = session.get(Product, product_id)
        if not product:
            return None

        for field, value in updates.items():
            if field not in allowed:
                continue
            if field in numeric_non_negative:
                try:
                    if float(value) < 0:
                        raise ValueError(f"{field} cannot be negative")
                except (TypeError, ValueError):
                    raise ValueError(f"Invalid value for {field}")
            setattr(product, field, value)

        session.flush()
        return {
            "id": product.id,
            "name": product.name,
            "category": product.category,
            "selling_price": float(product.selling_price),
            "cost_price": float(product.cost_price),
            "stock_quantity": product.stock_quantity,
        }

    @staticmethod
    def create_sale(
        session,
        user_id: str,
        items: list,
        payment_method: str,
        device_id: str,
        client_transaction_id: str,


    ) -> dict:

        existing = session.execute(
            select(Sale).where(Sale.client_transaction_id == client_transaction_id)
        ).scalar_one_or_none()
        if existing:
            existing_items = session.execute(
                select(SaleItem).where(SaleItem.sale_id == existing.id)
            ).scalars().all()
            return _serialize_sale(existing, existing_items)

        _validate_payment(payment_method)
        now = datetime.utcnow()
        items = _normalize_items(items)

        product_map = {}
        for item in items:
            product = session.get(Product, item["product_id"])
            if not product or not product.is_active:
                raise InsufficientStockError(product.name if product else "Unknown", item["product_id"])
            if product.stock_quantity < item["quantity"]:
                raise InsufficientStockError(product.name, product.id)
            product_map[product.id] = product

        total_amount = Decimal("0.00")
        profit_at_sale = Decimal("0.00")

        sale = Sale(
            id=str(uuid.uuid4()),
            client_transaction_id=client_transaction_id,
            device_id=device_id,
            receipt_number=_generate_receipt_number(session),
            user_id=user_id,
            total_amount=Decimal("0.00"),
            profit_at_sale=Decimal("0.00"),
    payment_method=payment_method,
            status="completed",
            created_at=now,
            editable_until=now + timedelta(minutes=20),
        )
        session.add(sale)

        try:
            session.flush()
        except IntegrityError:
            # If we're inside a caller-managed SAVEPOINT (e.g. process_queue()'s
            # per-item nested transaction), only roll back that savepoint —
            # NEVER the whole session. A full session.rollback() here would
            # discard every other pending change in the batch, including
            # SyncQueue row updates from transactions already processed
            # earlier in the same loop, causing "instance has been deleted"
            # errors on subsequent items in the same request.
            if session.in_nested_transaction():
                session.get_nested_transaction().rollback()
            else:
                session.rollback()

            existing = session.execute(
                select(Sale).where(Sale.client_transaction_id == client_transaction_id)
            ).scalar_one_or_none()
            if existing:
                existing_items = session.execute(
                    select(SaleItem).where(SaleItem.sale_id == existing.id)
                ).scalars().all()
                return _serialize_sale(existing, existing_items)
            raise

        for item in items:
            product = product_map[item["product_id"]]
            qty = item["quantity"]
            unit_price = Decimal(str(product.selling_price))
            cost_price = Decimal(str(product.cost_price))
            total_price = unit_price * qty
            total_amount += total_price
            profit_at_sale += (unit_price - cost_price) * qty

            session.add(SaleItem(
                id=str(uuid.uuid4()),
                sale_id=sale.id,
                product_id=product.id,
                quantity=qty,
                unit_price=unit_price,
                cost_price_at_sale=cost_price,
                total_price=total_price,
            ))
            product.stock_quantity -= qty
            session.add(InventoryLog(
                id=str(uuid.uuid4()),
                product_id=product.id,
                change_type="sale",
                quantity_change=-qty,
                reference_id=sale.id,
                created_at=now,
            ))

        sale.total_amount = total_amount
        sale.profit_at_sale = profit_at_sale
        session.flush()

        sale_items = session.execute(
            select(SaleItem).where(SaleItem.sale_id == sale.id)
        ).scalars().all()

        _create_audit_log(session, user_id, "CREATE_SALE", "sale", sale.id, {
            "receipt_number": sale.receipt_number,
            "total_amount": float(total_amount),
        "payment_method": payment_method,
        })

        return _serialize_sale(sale, sale_items)

    @staticmethod
    def get_sale(session, sale_id: str) -> dict | None:
        sale = session.get(Sale, sale_id)
        if not sale:
            return None
        items = session.execute(
            select(SaleItem).where(SaleItem.sale_id == sale_id)
        ).scalars().all()
        return _serialize_sale(sale, items)

    @staticmethod
    def edit_sale(session, sale_id: str, user_id: str, role: str, items: list, payment_method: str) -> dict:
        _validate_payment(payment_method)
        sale = session.get(Sale, sale_id)
        if not sale:
            raise ValueError("Sale not found")

        if sale.status == "cancelled":
            raise ValueError("Cannot edit a cancelled sale")

        now = datetime.utcnow()
        if role not in {"manager", "admin"} and now > sale.editable_until:
            raise PermissionError("edit_window_closed")

        items = _normalize_items(items)

        current_items = session.execute(
            select(SaleItem).where(SaleItem.sale_id == sale_id)
        ).scalars().all()
        current_qty_map = {i.product_id: i.quantity for i in current_items}
        new_product_ids = {item["product_id"] for item in items}

        product_map = {}
        for item in items:
            product = session.get(Product, item["product_id"])
            if not product or not product.is_active:
                raise InsufficientStockError(product.name if product else "Unknown", item["product_id"])
            current_qty = current_qty_map.get(product.id, 0)
            delta = item["quantity"] - current_qty
            if delta > 0 and product.stock_quantity < delta:
                raise InsufficientStockError(product.name, product.id)
            product_map[product.id] = (product, delta)



        removed_product_ids = set(current_qty_map.keys()) - new_product_ids
        for pid in removed_product_ids:
            product = session.get(Product, pid)
            if product:
                restored_qty = current_qty_map[pid]
                product.stock_quantity += restored_qty
                session.add(InventoryLog(
                    id=str(uuid.uuid4()),
                    product_id=product.id,
                    change_type="sale_edit",
                    quantity_change=restored_qty,
                    reference_id=sale.id,
                    created_at=now,
                ))

        for old_item in current_items:
            session.delete(old_item)
        session.flush()

        total_amount = Decimal("0.00")
        profit_at_sale = Decimal("0.00")

        for item in items:
            product, delta = product_map[item["product_id"]]
            qty = item["quantity"]
            unit_price = Decimal(str(product.selling_price))
            cost_price = Decimal(str(product.cost_price))
            total_price = unit_price * qty
            total_amount += total_price
            profit_at_sale += (unit_price - cost_price) * qty

            session.add(SaleItem(
                id=str(uuid.uuid4()),
                sale_id=sale.id,
                product_id=product.id,
                quantity=qty,
                unit_price=unit_price,
                cost_price_at_sale=cost_price,
                total_price=total_price,
            ))

            product.stock_quantity -= delta
            if delta != 0:
                session.add(InventoryLog(
                    id=str(uuid.uuid4()),
                    product_id=product.id,
                    change_type="sale_edit",
                    quantity_change=-delta,
                    reference_id=sale.id,
                    created_at=now,
                ))
=======
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from backend.models.models import Sale, SaleItem, Product, InventoryLog, AuditLog, User
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
            created_at=now_utc(),
            editable_until=now_utc() + timedelta(minutes=20)
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
        sale = session.query(Sale).options(joinedload(Sale.items).joinedload(SaleItem.product)).filter_by(id=sale_id).first()
        if not sale:
            return None, "Sale not found"
        return sale, None

    @staticmethod
    def get_all_sales(session: Session, user_id: str = None, role: str = None):
        query = session.query(Sale).options(joinedload(Sale.items).joinedload(SaleItem.product))
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
            product = session.query(Product).filter_by(id=old_item.product_id).first()
            if product:
                product.stock_quantity += old_item.quantity
                session.add(product)
                session.add(InventoryLog(
                    product_id=product.id,
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
                created_at=now_utc()
            ))
            product.stock_quantity -= quantity
            session.add(product)
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808

        sale.total_amount = total_amount
        sale.profit_at_sale = profit_at_sale
        sale.payment_method = payment_method
<<<<<<< HEAD

        sale.status = "edited"
        session.flush()

        new_items = session.execute(
            select(SaleItem).where(SaleItem.sale_id == sale.id)
        ).scalars().all()

        _create_audit_log(session, user_id, "EDIT_SALE", "sale", sale.id, {
            "edited_by_role": role,
            "new_total": float(total_amount),
    
        "payment_method": payment_method,
        })

        return _serialize_sale(sale, new_items)

    @staticmethod
    def cancel_sale(session, sale_id: str, user_id: str, role: str) -> dict:
        sale = session.get(Sale, sale_id)
        if not sale:
            raise ValueError("Sale not found")

        if sale.status == "cancelled":
            raise ValueError("Sale is already cancelled")

        items = session.execute(
            select(SaleItem).where(SaleItem.sale_id == sale_id)
        ).scalars().all()

        now = datetime.utcnow()
        for item in items:
            product = session.get(Product, item.product_id)
            if product:
                product.stock_quantity += item.quantity
                session.add(InventoryLog(
                    id=str(uuid.uuid4()),
=======
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
        for item in sale.items:
            product = session.query(Product).filter_by(id=item.product_id).first()
            if product:
                product.stock_quantity += item.quantity
                session.add(product)
                session.add(InventoryLog(
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
                    product_id=product.id,
                    change_type="cancellation",
                    quantity_change=item.quantity,
                    reference_id=sale.id,
<<<<<<< HEAD
                    created_at=now,
                ))

        sale.status = "cancelled"
        session.flush()

        _create_audit_log(session, user_id, "CANCEL_SALE", "sale", sale.id, {
            "cancelled_by_role": role,
        })

        return _serialize_sale(sale, items)

    
=======
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
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
