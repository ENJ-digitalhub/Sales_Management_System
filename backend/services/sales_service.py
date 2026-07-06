# backend/services/sales_service.py
from sqlalchemy import select, func
from datetime import datetime, timedelta

from backend.models.models import Product, Sale, SalesItem, AuditLogs


class InsufficientStockError(Exception):
    def __init__(self, product_id, message="Insufficient stock"):
        self.product_id = product_id
        super().__init__(message)


class SalesService:

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

    @staticmethod
    def create_sale(session, user_id, items, payment_method):
        if not items:
            raise ValueError("Items cannot be empty")

        with session.begin():
            product_ids = [i["product_id"] for i in items]

            products = session.execute(
                select(Product)
                .where(Product.id.in_(product_ids))
                .with_for_update()
            ).scalars().all()

            product_map = {p.id: p for p in products}

            if len(product_map) != len(set(product_ids)):
                raise ValueError("Some products not found")

            total_amount = 0
            total_profit = 0
            line_items = []

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

                line_items.append({
                    "product_id": pid,
                    "quantity": qty,
                    "unit_price": product.selling_price,
                    "cost_price_at_sale": product.cost_price,
                    "total_price": line_total,
                })

            sale = Sale(
                receipt_number=f"R-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
                user_id=user_id,
                total_amount=total_amount,
                profit_at_sale=total_profit,
                payment_method=payment_method,
                status="completed",
                editable_until=datetime.utcnow() + timedelta(minutes=20),
            )
            session.add(sale)
            session.flush()  # need sale.id for the FK rows below

            for li in line_items:
                session.add(SalesItem(sale_id=sale.id, **li))

            session.add(AuditLogs(
                user_id=user_id,
                action_type="create_sale",
                entity_type="sale",
                entity_id=sale.id,
                log_metadata=None,
            ))

        return SalesService.get_sale(session, sale.id)

    @staticmethod
    def get_sale(session, sale_id):
        sale = session.get(Sale, sale_id)
        if not sale:
            return None

        items = session.execute(
            select(SalesItem).where(SalesItem.sale_id == sale_id)
        ).scalars().all()

        return SalesService._serialize_sale(sale, items)

    @staticmethod
    def edit_sale(session, sale_id, user_id, role, items, payment_method):
        sale = session.get(Sale, sale_id)
        if not sale:
            raise ValueError("Sale not found")

        now = datetime.utcnow()
        if role not in ("manager", "admin") and now >= sale.editable_until:
            raise PermissionError("edit_window_closed")

        existing_items = session.execute(
            select(SalesItem).where(SalesItem.sale_id == sale_id)
        ).scalars().all()

        old_map = {i.product_id: i for i in existing_items}
        new_map = {i["product_id"]: i["quantity"] for i in items}
        all_product_ids = set(old_map) | set(new_map)

        products = session.execute(
            select(Product)
            .where(Product.id.in_(all_product_ids))
            .with_for_update()
        ).scalars().all()
        product_map = {p.id: p for p in products}

        total_amount = 0
        total_profit = 0

        for pid in all_product_ids:
            old_qty = old_map[pid].quantity if pid in old_map else 0
            new_qty = new_map.get(pid, 0)
            delta = new_qty - old_qty
            product = product_map[pid]

            if delta > 0:
                if product.stock_quantity < delta:
                    raise InsufficientStockError(pid)
                product.stock_quantity -= delta
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
                    item.unit_price = product.selling_price
                    item.cost_price_at_sale = product.cost_price
                    item.total_price = line_total
                else:
                    session.add(SalesItem(
                        sale_id=sale.id,
                        product_id=pid,
                        quantity=new_qty,
                        unit_price=product.selling_price,
                        cost_price_at_sale=product.cost_price,
                        total_price=line_total,
                    ))

        for pid in list(old_map):
            if pid not in new_map:
                session.delete(old_map[pid])

        sale.total_amount = total_amount
        sale.profit_at_sale = total_profit
        sale.payment_method = payment_method
        sale.status = "edited"

        session.add(AuditLogs(
            user_id=user_id,
            action_type="edit_sale",
            entity_type="sale",
            entity_id=sale.id,
            log_metadata=None,
        ))

        return SalesService.get_sale(session, sale.id)

    @staticmethod
    def cancel_sale(session, sale_id, user_id, role):
        if role not in ("manager", "admin"):
            raise ValueError("Only managers/admins can cancel sales")

        sale = session.get(Sale, sale_id)
        if not sale:
            raise ValueError("Sale not found")

        items = session.execute(
            select(SalesItem).where(SalesItem.sale_id == sale_id)
        ).scalars().all()

        product_ids = [i.product_id for i in items]
        products = session.execute(
            select(Product)
            .where(Product.id.in_(product_ids))
            .with_for_update()
        ).scalars().all()
        product_map = {p.id: p for p in products}

        for item in items:
            product_map[item.product_id].stock_quantity += item.quantity

        sale.status = "cancelled"

        session.add(AuditLogs(
            user_id=user_id,
            action_type="cancel_sale",
            entity_type="sale",
            entity_id=sale.id,
            log_metadata=None,
        ))

        return {"id": sale.id, "status": "cancelled"}

    @staticmethod
    def _serialize_sale(sale, items):
        return {
            "id": sale.id,
            "receipt_number": sale.receipt_number,
            "user_id": sale.user_id,
            "total_amount": float(sale.total_amount),
            "profit_at_sale": float(sale.profit_at_sale),
            "payment_method": sale.payment_method,
            "status": sale.status,
            "created_at": sale.created_at.isoformat(),
            "editable_until": sale.editable_until.isoformat(),
            "items": [
                {
                    "product_id": i.product_id,
                    "quantity": i.quantity,
                    "unit_price": float(i.unit_price),
                    "total_price": float(i.total_price),
                }
                for i in items
            ],
        }