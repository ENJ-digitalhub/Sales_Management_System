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