
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from backend.models.models import SyncQueue, User, Product, Sale, SaleItem, Purchase, PurchaseItem, Device, AuditLog, InventoryLog
from datetime import datetime, timezone
from typing import Any
import json


def _coerce_payload(payload: Any) -> dict[str, Any] | str:
    if isinstance(payload, str):
        try:
            parsed = json.loads(payload)
            if isinstance(parsed, dict):
                return parsed
            return payload
        except json.JSONDecodeError:
            return payload
    if isinstance(payload, (bytes, bytearray)):
        try:
            decoded = payload.decode("utf-8")
            parsed = json.loads(decoded)
            if isinstance(parsed, dict):
                return parsed
            return decoded
        except (UnicodeDecodeError, json.JSONDecodeError):
            return payload.decode("utf-8") if isinstance(payload, (bytes, bytearray)) else payload
    if isinstance(payload, dict):
        return payload
    return payload


class SyncService:
    @staticmethod
    def enqueue_change(session: Session, device_id: str, transaction_id: str, entity_type: str, operation: str, payload: dict):
        existing = session.query(SyncQueue).filter_by(transaction_id=transaction_id).first()
        if existing:
            return existing, "duplicate"

        sync_entry = SyncQueue(
            transaction_id=transaction_id,
            device_id=device_id,
            entity_type=entity_type,
            operation=operation,
            payload=json.dumps(payload),
            status="pending",
            created_at=datetime.now(timezone.utc)
        )
        session.add(sync_entry)
        return sync_entry, None

    @staticmethod
    def process_sync_queue(session: Session, device_id: str):
        # Fetch pending items for this device
        pending_items = session.query(SyncQueue).filter_by(device_id=device_id, status="pending").order_by(SyncQueue.created_at).all()
        processed_results = []

        for item in pending_items:
            try:
                payload = _coerce_payload(item.payload)
                if not isinstance(payload, dict):
                    raise ValueError("Sync payload must be a dictionary")

                # Apply changes based on entity_type and operation
                # This is a simplified example; real-world would need more robust logic
                if item.entity_type == "product":
                    if item.operation == "CREATE":
                        product = Product(**payload)
                        session.add(product)
                    elif item.operation == "UPDATE":
                        product_id = payload.get("id")
                        if not product_id:
                            raise ValueError("Product update payload is missing an id")
                        update_data = {
                            getattr(Product, key): value
                            for key, value in payload.items()
                            if key != "id" and hasattr(Product, key)
                        }
                        session.query(Product).filter_by(id=str(product_id)).update(update_data)
                    elif item.operation == "DELETE":
                        product_id = payload.get("id")
                        if not product_id:
                            raise ValueError("Product delete payload is missing an id")
                        session.query(Product).filter_by(id=str(product_id)).update({"is_active": False})
                # Add similar logic for other entity types (User, Sale, Purchase, etc.)

                item.status = "synced"
                processed_results.append({"transaction_id": item.transaction_id, "status": "success"})
            except Exception as e:
                item.status = "failed"
                item.retry_count += 1
                item.last_attempt_at = datetime.now(timezone.utc)
                processed_results.append({"transaction_id": item.transaction_id, "status": "failed", "error": str(e)})
            session.add(item)

        session.commit()
        return processed_results

    @staticmethod
    def get_unsynced_changes(session: Session, last_sync_time: datetime):
        # This would fetch changes from the server's perspective to send to client
        # For simplicity, let's assume we send all changes since last_sync_time
        # In a real system, this would involve versioning or change tracking tables
        new_products = session.query(Product).filter(Product.updated_at > last_sync_time).all()
        new_sales = session.query(Sale).filter(Sale.created_at > last_sync_time).all()
        # ... and so on for other entities

        changes = {
            "products": [p.to_dict() for p in new_products],
            "sales": [s.to_dict() for s in new_sales],
            # Add other entities
        }
        return changes

    @staticmethod
    def resolve_conflict(session: Session, transaction_id: str, resolution_payload: dict):
        # Delegate conflict resolution to the shared sync queue engine.
        # Currently `resolution_payload` is expected to be a dict with at least:
        # {"transaction_id": ..., "resolution": "approve" | "reject", "note": "..."}
        resolution = resolution_payload.get("resolution")
        note = resolution_payload.get("note")
        user_id = resolution_payload.get("resolved_by")
        if not transaction_id or resolution not in ["approve", "reject"]:
            return None, "Invalid resolution payload"
        if not user_id:
            return None, "Resolved by user id is required"

        from backend.sync.queue import Queue
        return Queue().resolve_conflict(transaction_id, resolution, user_id, note, session)
