import re
import uuid
from datetime import datetime
from sqlalchemy import select
from backend.models.models import Product, AuditLog


def _generate_sku(name: str) -> str:
    """Auto-generates a SKU since the Phase 4 API contract doesn't accept
    one from the client, but Product.sku is NOT NULL + unique at the
    model level. Deterministic-ish prefix from the name + random suffix
    keeps it human-readable while guaranteeing uniqueness."""
    slug = re.sub(r'[^A-Z0-9]', '', name.upper())[:6] or "PROD"
    suffix = str(uuid.uuid4())[:8].upper()
    return f"SKU-{slug}-{suffix}"


def _serialize_product(product) -> dict:
    return {
        "id": product.id,
        "name": product.name,
        "sku": product.sku,
        "category": product.category,
        "selling_price": float(product.selling_price),
        "cost_price": float(product.cost_price),
        "stock_quantity": product.stock_quantity,
        "is_active": bool(product.is_active),
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
    }


def _create_audit_log(session, user_id: str, action_type: str, entity_id: str, metadata: dict = None):
    session.add(AuditLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        action_type=action_type,
        entity_type="product",
        entity_id=entity_id,
        log_metadata=metadata or {},
        created_at=datetime.utcnow(),
    ))


class ProductsService:
    @staticmethod
    def get_all_products(session, include_inactive: bool = False) -> list[dict]:
        query = select(Product)
        if not include_inactive:
            query = query.where(Product.is_active == 1)
        products = session.execute(query).scalars().all()
        return [_serialize_product(p) for p in products]

    @staticmethod
    def create_product(session, user_id: str, fields: dict) -> dict:
        # Duplicate-name guard intentionally omitted — only sku is unique
        # at the model level, and sku isn't part of this payload.
        product = Product(
            id=str(uuid.uuid4()),
            name=fields["name"].strip(),
            sku=_generate_sku(fields["name"]),
            category=fields.get("category"),
            selling_price=fields["selling_price"],
            cost_price=fields["cost_price"],
            stock_quantity=fields["stock_quantity"],
            is_active=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(product)
        session.flush()

        _create_audit_log(session, user_id, "CREATE_PRODUCT", product.id, {
            "name": product.name,
            "sku": product.sku,
            "selling_price": float(product.selling_price),
            "cost_price": float(product.cost_price),
            "stock_quantity": product.stock_quantity,
        })

        return _serialize_product(product)

    @staticmethod
    def edit_product(session, user_id: str, product_id: str, fields: dict) -> dict | None:
        product = session.get(Product, product_id)
        if not product:
            return None

        before = {
            "name": product.name,
            "category": product.category,
            "selling_price": float(product.selling_price),
            "cost_price": float(product.cost_price),
            "stock_quantity": product.stock_quantity,
        }

        if "name" in fields:
            product.name = fields["name"].strip()
        if "category" in fields:
            product.category = fields["category"]
        if "selling_price" in fields:
            product.selling_price = fields["selling_price"]
        if "cost_price" in fields:
            product.cost_price = fields["cost_price"]
        if "stock_quantity" in fields:
            product.stock_quantity = fields["stock_quantity"]

        product.updated_at = datetime.utcnow()
        session.flush()

        _create_audit_log(session, user_id, "EDIT_PRODUCT", product.id, {
            "before": before,
            "after": {
                "name": product.name,
                "category": product.category,
                "selling_price": float(product.selling_price),
                "cost_price": float(product.cost_price),
                "stock_quantity": product.stock_quantity,
            },
        })

        return _serialize_product(product)

    @staticmethod
    def deactivate_product(session, user_id: str, product_id: str) -> dict | None:
        product = session.get(Product, product_id)
        if not product:
            return None

        if product.is_active == 0:
            # Already inactive — idempotent success, not an error.
            return _serialize_product(product)

        product.is_active = 0
        product.updated_at = datetime.utcnow()
        session.flush()

        _create_audit_log(session, user_id, "DEACTIVATE_PRODUCT", product.id, {
            "name": product.name,
        })

        return _serialize_product(product)