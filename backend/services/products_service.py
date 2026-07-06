
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.models.models import Product, AuditLog, InventoryLog
from datetime import datetime, timezone
from decimal import Decimal
import uuid

class ProductService:
    @staticmethod
    def create_product(session: Session, user_id: str, name: str, category: str, selling_price: Decimal, cost_price: Decimal, stock_quantity: int):
        product = Product(
            id=str(uuid.uuid4()),
            name=name,
            category=category,
            selling_price=selling_price,
            cost_price=cost_price,
            stock_quantity=stock_quantity,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(product)

        session.add(AuditLog(
            user_id=user_id,
            action_type="create_product",
            entity_type="product",
            entity_id=product.id,
            log_metadata={"name": name, "category": category, "selling_price": str(selling_price), "cost_price": str(cost_price), "stock_quantity": stock_quantity},
            created_at=datetime.now(timezone.utc)
        ))

        session.add(InventoryLog(
            product_id=product.id,
            change_type="restock",
            quantity_change=stock_quantity,
            reference_id=product.id,
            created_at=datetime.now(timezone.utc)
        ))

        session.commit()
        return product, None

    @staticmethod
    def get_product(session: Session, product_id: str):
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            return None, "Product not found"
        return product, None

    @staticmethod
    def get_all_products(session: Session):
        products = session.query(Product).filter_by(is_active=True).all()
        return products, None

    @staticmethod
    def update_product(session: Session, product_id: str, user_id: str, name: str = None, category: str = None, selling_price: Decimal = None, cost_price: Decimal = None, stock_quantity: int = None, is_active: bool = None):
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            return None, "Product not found"

        old_data = product.to_dict()
        updated_fields = {}

        if name is not None: product.name = name; updated_fields["name"] = name
        if category is not None: product.category = category; updated_fields["category"] = category
        if selling_price is not None: product.selling_price = selling_price; updated_fields["selling_price"] = str(selling_price)
        if cost_price is not None: product.cost_price = cost_price; updated_fields["cost_price"] = str(cost_price)
        if is_active is not None: product.is_active = is_active; updated_fields["is_active"] = is_active

        if stock_quantity is not None and stock_quantity != product.stock_quantity:
            change = stock_quantity - product.stock_quantity
            product.stock_quantity = stock_quantity
            updated_fields["stock_quantity"] = stock_quantity
            session.add(InventoryLog(
                product_id=product.id,
                change_type="adjustment",
                quantity_change=change,
                reference_id=product.id,
                created_at=datetime.now(timezone.utc)
            ))

        product.updated_at = datetime.now(timezone.utc)
        session.add(product)

        session.add(AuditLog(
            user_id=user_id,
            action_type="edit_product",
            entity_type="product",
            entity_id=product.id,
            log_metadata={"old_data": old_data, "updated_fields": updated_fields},
            created_at=datetime.now(timezone.utc)
        ))

        session.commit()
        return product, None

    @staticmethod
    def delete_product(session: Session, product_id: str, user_id: str):
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            return None, "Product not found"

        product.is_active = False
        product.updated_at = datetime.now(timezone.utc)
        session.add(product)

        session.add(AuditLog(
            user_id=user_id,
            action_type="delete_product",
            entity_type="product",
            entity_id=product.id,
            log_metadata={"status": "deactivated"},
            created_at=datetime.now(timezone.utc)
        ))

        session.commit()
        return True, None

# Helper for Product to_dict
def to_dict(self):
    return {
        "id": self.id,
        "name": self.name,
        "category": self.category,
        "selling_price": float(self.selling_price),
        "cost_price": float(self.cost_price),
        "stock_quantity": self.stock_quantity,
        "is_active": self.is_active,
        "created_at": self.created_at.isoformat(),
        "updated_at": self.updated_at.isoformat()
    }