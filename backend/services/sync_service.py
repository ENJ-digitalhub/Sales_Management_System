
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from backend.models.models import SyncQueue, User, Product, Sale, SaleItem, Purchase, PurchaseItem, Device, AuditLog, InventoryLog
from datetime import datetime, timezone
import json

class SyncService:
    @staticmethod
    def enqueue_change(session: Session, device_id: str, entity_type: str, operation: str, payload: dict):
        transaction_id = f"{device_id}-{entity_type}-{operation}-{datetime.now(timezone.utc).isoformat()}"
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
        return sync_entry

    @staticmethod
    def process_sync_queue(session: Session, device_id: str):
        # Fetch pending items for this device
        pending_items = session.query(SyncQueue).filter_by(device_id=device_id, status="pending").order_by(SyncQueue.created_at).all()
        processed_results = []

        for item in pending_items:
            try:
                payload = json.loads(item.payload)
                # Apply changes based on entity_type and operation
                # This is a simplified example; real-world would need more robust logic
                if item.entity_type == "product":
                    if item.operation == "CREATE":
                        product = Product(**payload)
                        session.add(product)
                    elif item.operation == "UPDATE":
                        session.query(Product).filter_by(id=payload["id"]).update(payload)
                    elif item.operation == "DELETE":
                        session.query(Product).filter_by(id=payload["id"]).update({"is_active": False})
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
        # This is where conflict resolution logic would go
        # For now, we'll just mark the original item as resolved and apply the new payload
        sync_item = session.query(SyncQueue).filter_by(transaction_id=transaction_id).first()
        if not sync_item:
            return None, "Sync item not found"

        sync_item.status = "resolved"
        sync_item.payload = json.dumps(resolution_payload)
        # Re-enqueue or apply directly based on resolution strategy
        # For simplicity, let's just update the status and assume the client will re-push
        session.add(sync_item)
        session.commit()
        return sync_item, None
