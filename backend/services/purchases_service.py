import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select
from backend.models.models import Purchase, PurchaseItem, Product, InventoryLog, AuditLog


class ProductNotFoundError(Exception):
    def __init__(self, product_id: str):
        self.product_id = product_id
        super().__init__(f"Product not found: {product_id}")


class PurchaseNotFoundError(Exception):
    pass


class PurchaseAlreadyProcessedError(Exception):
    def __init__(self, status: str):
        self.status = status
        super().__init__(f"Purchase already {status}")


def _serialize_purchase(purchase, items) -> dict:
    return {
        "id": purchase.id,
        "status": purchase.status,
        "supplier": purchase.supplier,
        "total_cost": float(purchase.total_cost),
        "created_by": purchase.created_by,
        "created_at": purchase.created_at.isoformat() if purchase.created_at else None,
        "approved_by": purchase.approved_by,
        "approved_at": purchase.approved_at.isoformat() if purchase.approved_at else None,
        "items": [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "cost_price": float(item.unit_cost),
                "line_total": float(item.line_total),
            }
            for item in items
        ],
    }


def _create_audit_log(session, user_id: str, action_type: str, entity_id: str, metadata: dict = None):
    session.add(AuditLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        action_type=action_type,
        entity_type="purchase",
        entity_id=entity_id,
        log_metadata=metadata or {},
        created_at=datetime.utcnow(),
    ))


class PurchasesService:
    @staticmethod
    def create_purchase(session, user_id: str, items: list, supplier: str = None) -> dict:
        """
        Creates a pending purchase. Does NOT touch stock — stock only
        changes on approval, per the locked business rule.
        """
        # Verify every product exists up front — fail the whole purchase
        # before creating anything if any product_id is invalid.
        product_ids = {item["product_id"] for item in items}
        found_products = session.execute(
            select(Product.id).where(Product.id.in_(product_ids))
        ).scalars().all()
        missing = product_ids - set(found_products)
        if missing:
            raise ProductNotFoundError(next(iter(missing)))

        total_cost = Decimal("0.00")
        purchase = Purchase(
            id=str(uuid.uuid4()),
            created_by=user_id,
            supplier=supplier,
            status="pending",
            total_cost=Decimal("0.00"),
            created_at=datetime.utcnow(),
        )
        session.add(purchase)
        session.flush()

        for item in items:
            unit_cost = Decimal(str(item["cost_price"]))
            qty = item["quantity"]
            line_total = unit_cost * qty
            total_cost += line_total

            session.add(PurchaseItem(
                id=str(uuid.uuid4()),
                purchase_id=purchase.id,
                product_id=item["product_id"],
                quantity=qty,
                unit_cost=unit_cost,
                line_total=line_total,
            ))

        purchase.total_cost = total_cost
        session.flush()

        purchase_items = session.execute(
            select(PurchaseItem).where(PurchaseItem.purchase_id == purchase.id)
        ).scalars().all()

        _create_audit_log(session, user_id, "CREATE_PURCHASE", purchase.id, {
            "supplier": supplier,
            "total_cost": float(total_cost),
            "item_count": len(items),
        })

        return _serialize_purchase(purchase, purchase_items)

    @staticmethod
    def approve_purchase(session, purchase_id: str, admin_id: str) -> dict:
        """
        Increments stock for every item in the purchase, logs each stock
        movement, and marks the purchase approved. All-or-nothing: if any
        product referenced by the purchase no longer exists, the entire
        approval fails and nothing is changed — a purchase shouldn't be
        partially approved, since that leaves the record in an ambiguous
        state that's hard to reason about or reverse.
        """
        purchase = session.get(Purchase, purchase_id)
        if not purchase:
            raise PurchaseNotFoundError(purchase_id)

        if purchase.status != "pending":
            raise PurchaseAlreadyProcessedError(purchase.status)

        items = session.execute(
            select(PurchaseItem).where(PurchaseItem.purchase_id == purchase_id)
        ).scalars().all()

        # Verify every product still exists before changing anything.
        product_map = {}
        for item in items:
            product = session.get(Product, item.product_id)
            if not product:
                raise ProductNotFoundError(item.product_id)
            product_map[item.product_id] = product

        now = datetime.utcnow()
        for item in items:
            product = product_map[item.product_id]
            product.stock_quantity += item.quantity
            product.updated_at = now

            session.add(InventoryLog(
                id=str(uuid.uuid4()),
                product_id=product.id,
                change_type="restock",
                quantity_change=item.quantity,
                reference_id=purchase.id,
                created_at=now,
            ))

        purchase.status = "approved"
        purchase.approved_by = admin_id
        purchase.approved_at = now
        session.flush()

        _create_audit_log(session, admin_id, "APPROVE_PURCHASE", purchase.id, {
            "total_cost": float(purchase.total_cost),
            "item_count": len(items),
        })

        return {
            "success": True,
            "message": "Purchase approved. Stock updated.",
            "purchase_id": purchase.id,
        }

    @staticmethod
    def get_purchase(session, purchase_id: str) -> dict | None:
        purchase = session.get(Purchase, purchase_id)
        if not purchase:
            return None
        items = session.execute(
            select(PurchaseItem).where(PurchaseItem.purchase_id == purchase_id)
        ).scalars().all()
        return _serialize_purchase(purchase, items)

    @staticmethod
    def get_purchase_history(session) -> list[dict]:
        purchases = session.execute(
            select(Purchase).order_by(Purchase.created_at.desc())
        ).scalars().all()

        result = []
        for purchase in purchases:
            items = session.execute(
                select(PurchaseItem).where(PurchaseItem.purchase_id == purchase.id)
            ).scalars().all()
            result.append(_serialize_purchase(purchase, items))
        return result