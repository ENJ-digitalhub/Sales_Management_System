<<<<<<< HEAD
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from backend.models.models import Sale, SaleItem, Product, InventoryLog, AuditLog
from backend.utils.validators import (
    ALLOWED_PAYMENT_METHODS,
    SUPPORTED_PAYMENT_PROVIDERS,
    PROVIDER_REQUIRED_METHODS,
    SPLIT_METHOD,
)


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
        "payment_provider": sale.payment_provider,
        "payment_details": sale.payment_details,
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
    log = AuditLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        log_metadata=metadata or {},
        created_at=datetime.utcnow(),
    )
    session.add(log)


def _normalize_items(items: list) -> list:
    agg = {}
    for item in items:
        pid = item["product_id"]
        qty = int(item["quantity"])
        if qty <= 0:
            raise ValueError("Quantity must be a positive integer")
        agg[pid] = agg.get(pid, 0) + qty
    return [{"product_id": pid, "quantity": qty} for pid, qty in agg.items()]


def _validate_payment(payment_method: str, payment_provider: str = None, payment_details=None):
    """Defense-in-depth re-check, using the same constants as validators.py
    (imported, not duplicated) so the two can never drift apart."""
    if payment_method not in ALLOWED_PAYMENT_METHODS:
        raise ValueError("Invalid payment_method")

    if payment_method == SPLIT_METHOD:
        if not isinstance(payment_details, list) or len(payment_details) == 0:
            raise ValueError("payment_details is required for split_payment")
        if payment_provider is not None:
            raise ValueError("payment_provider must not be set for split_payment")
        return

    if payment_method in PROVIDER_REQUIRED_METHODS and not payment_provider:
        raise ValueError(f"payment_provider is required for {payment_method}")

    if payment_provider is not None and payment_provider not in SUPPORTED_PAYMENT_PROVIDERS:
        raise ValueError("Invalid payment_provider")


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
        payment_provider: str = None,
        payment_details=None,
    ) -> dict:
        # Idempotency: if this exact client_transaction_id already produced
        # a sale (e.g. an offline sale retried after a failed sync), return
        # that sale instead of creating a duplicate.
        existing = session.execute(
            select(Sale).where(Sale.client_transaction_id == client_transaction_id)
        ).scalar_one_or_none()
        if existing:
            existing_items = session.execute(
                select(SaleItem).where(SaleItem.sale_id == existing.id)
            ).scalars().all()
            return _serialize_sale(existing, existing_items)

        _validate_payment(payment_method, payment_provider, payment_details)
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
            payment_provider=payment_provider,
            payment_details=payment_details,
            status="completed",
            created_at=now,
            editable_until=now + timedelta(minutes=20),
        )
        session.add(sale)

        try:
            session.flush()
        except IntegrityError:
            # Race: another request with the same client_transaction_id
            # committed between our SELECT above and this flush. Back off
            # and return whatever they created.
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
            "payment_provider": payment_provider,
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
    def edit_sale(session, sale_id: str, user_id: str, role: str, items: list, payment_method: str, payment_provider: str = None, payment_details=None) -> dict:
        _validate_payment(payment_method, payment_provider, payment_details)
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

        # Products that were in the sale before but are gone from the new
        # item list need their full old quantity restored to stock —
        # otherwise that stock is lost forever.
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

        sale.total_amount = total_amount
        sale.profit_at_sale = profit_at_sale
        sale.payment_method = payment_method
        sale.payment_provider = payment_provider
        sale.payment_details = payment_details
        sale.status = "edited"
        session.flush()

        new_items = session.execute(
            select(SaleItem).where(SaleItem.sale_id == sale.id)
        ).scalars().all()

        _create_audit_log(session, user_id, "EDIT_SALE", "sale", sale.id, {
            "edited_by_role": role,
            "new_total": float(total_amount),
            "payment_method": payment_method,
            "payment_provider": payment_provider,
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
                    product_id=product.id,
                    change_type="cancellation",
                    quantity_change=item.quantity,
                    reference_id=sale.id,
                    created_at=now,
                ))

        sale.status = "cancelled"
        session.flush()

        _create_audit_log(session, user_id, "CANCEL_SALE", "sale", sale.id, {
            "cancelled_by_role": role,
        })

        return _serialize_sale(sale, items)
=======
# backend/services/sales_service.py

from sqlalchemy import select, func
from datetime import datetime, timedelta

from backend.models.models import Product, Sale, SaleItem, AuditLog

class InsufficientStockError(Exception):
def init(self, product_id, message="Insufficient stock"):
self.product_id = product_id
super().init(message)

class SalesService:

# -----------------------------------
# PRODUCTS
# -----------------------------------
@staticmethod
def get_paginated_products(session, page: int, per_page: int):
    offset = (page - 1) * per_page

    total_count = session.execute(
        select(func.count(Product.id)).where(Product.is_active == True)
    ).scalar() or 0

    products = session.execute(
        select(Product)
        .where(Product.is_active == True)
        .offset(offset)
        .limit(per_page)
    ).scalars().all()

    return {
        "items": [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "selling_price": p.selling_price,
                "cost_price": p.cost_price,
                "stock_quantity": p.stock_quantity,
            }
            for p in products
        ],
        "total": total_count,
        "page": page,
        "per_page": per_page,
    }

# -----------------------------------
# CREATE SALE
# -----------------------------------
@staticmethod
def create_sale(...):
    if not items:
        raise ValueError("Items cannot be empty")

    with session.begin():  # ✅ THIS IS THE FIX

        product_ids = [i["product_id"] for i in items]

        products = session.execute(
            select(Product)
            .where(Product.id.in_(product_ids))
            .with_for_update()
        ).scalars().all()

        product_map = {p.id: p for p in products}

        if len(product_map) != len(product_ids):
            raise ValueError("Some products not found")

        total_amount = 0
        total_profit = 0
        sale_items = []

        for item in items:
            pid = item["product_id"]
            qty = item["quantity"]

            if qty <= 0:
                raise ValueError(f"Invalid quantity for product {pid}")

            product = product_map[pid]

            if product.stock_quantity < qty:
                raise InsufficientStockError(
                    product_id=pid,
                    message=f"Insufficient stock for {product.name}",
                )

            product.stock_quantity -= qty

            line_total = product.selling_price * qty
            profit = (product.selling_price - product.cost_price) * qty

            total_amount += line_total
            total_profit += profit

            sale_items.append(
                SaleItem(
                    product_id=pid,
                    quantity=qty,
                    unit_price=product.selling_price,
                    cost_price=product.cost_price,
                    total_price=line_total,
                    profit_at_sale=profit,
                )
            )

        sale = Sale(
            user_id=user_id,
            total_amount=total_amount,
            profit_at_sale=total_profit,
            payment_method=payment_method,
            payment_provider=payment_provider,
            payment_details=payment_details,
            device_id=device_id,
            client_transaction_id=client_transaction_id,
            editable_until=datetime.utcnow() + timedelta(minutes=20),
        )

        session.add(sale)
        session.flush()

        for si in sale_items:
            si.sale_id = sale.id
            session.add(si)

        session.add(AuditLog(
            action="SALE_CREATED",
            user_id=user_id,
            entity_type="sale",
            entity_id=sale.id,
        ))

        return SalesService._serialize_sale(sale, sale_items)
    
# -----------------------------------
# GET SALE
# -----------------------------------
@staticmethod
def get_sale(session, sale_id):
    sale = session.get(Sale, sale_id)
    if not sale:
        return None

    items = session.execute(
        select(SaleItem).where(SaleItem.sale_id == sale_id)
    ).scalars().all()

    return SalesService._serialize_sale(sale, items)

# -----------------------------------
# EDIT SALE
# -----------------------------------
@staticmethod
def edit_sale(
    session,
    sale_id,
    user_id,
    role,
    items,
    payment_method,
    payment_provider=None,
    payment_details=None,
):
    sale = session.get(Sale, sale_id)
    if not sale:
        raise ValueError("Sale not found")

    now = datetime.utcnow()

    # ⛔ Edit window check
    if role not in ("manager", "admin") and now >= sale.editable_until:
        raise PermissionError("edit_window_closed")

    # Lock products + existing items
    existing_items = session.execute(
        select(SaleItem).where(SaleItem.sale_id == sale_id)
    ).scalars().all()

    old_map = {i.product_id: i for i in existing_items}
    new_map = {i["product_id"]: i["quantity"] for i in items}

    all_product_ids = set(old_map.keys()) | set(new_map.keys())

    products = session.execute(
        select(Product)
        .where(Product.id.in_(all_product_ids))
        .with_for_update()
    ).scalars().all()

    product_map = {p.id: p for p in products}

    total_amount = 0
    total_profit = 0

    # 🔁 DELTA LOGIC
    for pid in all_product_ids:
        old_qty = old_map.get(pid).quantity if pid in old_map else 0
        new_qty = new_map.get(pid, 0)

        delta = new_qty - old_qty
        product = product_map[pid]

        # Increase → check stock
        if delta > 0:
            if product.stock_quantity < delta:
                raise InsufficientStockError(pid)
            product.stock_quantity -= delta

        # Decrease → restore stock
        elif delta < 0:
            product.stock_quantity += abs(delta)

        if new_qty > 0:
            line_total = product.selling_price * new_qty
            profit = (product.selling_price - product.cost_price) * new_qty

            total_amount += line_total
            total_profit += profit

            if pid in old_map:
                item = old_map[pid]
                item.quantity = new_qty
                item.total_price = line_total
                item.profit_at_sale = profit
            else:
                session.add(SaleItem(
                    sale_id=sale.id,
                    product_id=pid,
                    quantity=new_qty,
                    unit_price=product.selling_price,
                    cost_price=product.cost_price,
                    total_price=line_total,
                    profit_at_sale=profit,
                ))

    # Remove deleted items
    for pid in list(old_map.keys()):
        if pid not in new_map:
            session.delete(old_map[pid])

    sale.total_amount = total_amount
    sale.profit_at_sale = total_profit
    sale.payment_method = payment_method
    sale.payment_provider = payment_provider
    sale.payment_details = payment_details

    session.add(AuditLog(
        action="SALE_EDITED",
        user_id=user_id,
        entity_type="sale",
        entity_id=sale.id,
    ))

    return SalesService.get_sale(session, sale.id)

# -----------------------------------
# CANCEL SALE
# -----------------------------------
@staticmethod
def cancel_sale(session, sale_id, user_id, role):
    if role not in ("manager", "admin"):
        raise ValueError("Only managers/admins can cancel sales")

    sale = session.get(Sale, sale_id)
    if not sale:
        raise ValueError("Sale not found")

    items = session.execute(
        select(SaleItem).where(SaleItem.sale_id == sale_id)
    ).scalars().all()

    product_ids = [i.product_id for i in items]

    products = session.execute(
        select(Product)
        .where(Product.id.in_(product_ids))
        .with_for_update()
    ).scalars().all()

    product_map = {p.id: p for p in products}

    # Restore stock
    for item in items:
        product_map[item.product_id].stock_quantity += item.quantity

    sale.status = "cancelled"

    session.add(AuditLog(
        action="SALE_CANCELLED",
        user_id=user_id,
        entity_type="sale",
        entity_id=sale.id,
    ))

    return {"id": sale.id, "status": "cancelled"}

# -----------------------------------
# SERIALIZER
# -----------------------------------
@staticmethod
def _serialize_sale(sale, items):
    return {
        "id": sale.id,
        "user_id": sale.user_id,
        "total_amount": sale.total_amount,
        "profit_at_sale": sale.profit_at_sale,
        "payment_method": sale.payment_method,
        "editable_until": sale.editable_until.isoformat(),
        "items": [
            {
                "product_id": i.product_id,
                "quantity": i.quantity,
                "unit_price": i.unit_price,
                "total_price": i.total_price,
            }
            for i in items
        ],
    }
>>>>>>> 166f1ee040f599bc784a2737b4d4c28b35a3160b
