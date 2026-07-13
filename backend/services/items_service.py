
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.models.models import Item, AuditLog, InventoryLog
from datetime import datetime, timezone
from decimal import Decimal
import uuid

class ItemService:
    @staticmethod
    def create_item(session: Session, user_id: str, name: str, category: str, selling_price: Decimal, cost_price: Decimal, stock_quantity: int):
        item = Item(
            id=str(uuid.uuid4()),
            name=name,
            category=category,
            selling_price=selling_price,
            cost_price=cost_price,
            stock_quantity=stock_quantity,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(item)

        session.add(AuditLog(
            user_id=user_id,
            action_type="create_item",
            entity_type="item",
            entity_id=item.id,
            log_metadata={"name": name, "category": category, "selling_price": str(selling_price), "cost_price": str(cost_price), "stock_quantity": stock_quantity},
            created_at=datetime.now(timezone.utc)
        ))

        session.add(InventoryLog(
            item_id=item.id,
            change_type="restock",
            quantity_change=stock_quantity,
            reference_id=item.id,
            created_at=datetime.now(timezone.utc)
        ))

        session.commit()
        return item, None

    @staticmethod
    def get_item(session: Session, item_id: str):
        item = session.query(Item).filter_by(id=item_id).first()
        if not item:
            return None, "Item not found"
        return item, None

    @staticmethod
    def get_all_items(session: Session):
        items = session.query(Item).filter_by(is_active=True).all()
        return items, None

    @staticmethod
    def update_item(session: Session, item_id: str, user_id: str, name: str = None, category: str = None, selling_price: Decimal = None, cost_price: Decimal = None, stock_quantity: int = None, is_active: bool = None):
        item = session.query(Item).filter_by(id=item_id).first()
        if not item:
            return None, "Item not found"

        old_data = item.to_dict()
        updated_fields = {}

        if name is not None: item.name = name; updated_fields["name"] = name
        if category is not None: item.category = category; updated_fields["category"] = category
        if selling_price is not None: item.selling_price = selling_price; updated_fields["selling_price"] = str(selling_price)
        if cost_price is not None: item.cost_price = cost_price; updated_fields["cost_price"] = str(cost_price)
        if is_active is not None: item.is_active = is_active; updated_fields["is_active"] = is_active

        if stock_quantity is not None and stock_quantity != item.stock_quantity:
            change = stock_quantity - item.stock_quantity
            item.stock_quantity = stock_quantity
            updated_fields["stock_quantity"] = stock_quantity
            session.add(InventoryLog(
                item_id=item.id,
                change_type="adjustment",
                quantity_change=change,
                reference_id=item.id,
                created_at=datetime.now(timezone.utc)
            ))

        item.updated_at = datetime.now(timezone.utc)
        session.add(item)

        session.add(AuditLog(
            user_id=user_id,
            action_type="edit_item",
            entity_type="item",
            entity_id=item.id,
            log_metadata={"old_data": old_data, "updated_fields": updated_fields},
            created_at=datetime.now(timezone.utc)
        ))

        session.commit()
        return item, None

    @staticmethod
    def delete_item(session: Session, item_id: str, user_id: str):
        item = session.query(Item).filter_by(id=item_id).first()
        if not item:
            return None, "Item not found"

        item.is_active = False
        item.updated_at = datetime.now(timezone.utc)
        session.add(item)

        session.add(AuditLog(
            user_id=user_id,
            action_type="delete_item",
            entity_type="item",
            entity_id=item.id,
            log_metadata={"status": "deactivated"},
            created_at=datetime.now(timezone.utc)
        ))

        session.commit()
        return True, None