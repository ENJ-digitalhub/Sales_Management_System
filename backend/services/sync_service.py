<<<<<<< HEAD
import uuid
from datetime import datetime
from sqlalchemy import select
from backend.models.models import Product, User, AuditLog
from backend.sync.queue import push_to_queue, process_queue, resolve_conflict as engine_resolve_conflict

MAX_BATCH_SIZE = 20


class BatchTooLargeError(Exception):
    pass


class DeviceMismatchError(Exception):
    pass


def _create_audit_log(session, user_id, action_type, entity_id, metadata=None):
    session.add(AuditLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        action_type=action_type,
        entity_type="sync",
        entity_id=entity_id,
        log_metadata=metadata or {},
        created_at=datetime.utcnow(),
    ))
=======

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
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808


class SyncService:
    @staticmethod
<<<<<<< HEAD
    def push_sync(session, device_id: str, jwt_device_id: str, transactions: list, user_id: str) -> list:
        if device_id != jwt_device_id:
            raise DeviceMismatchError("device_id does not match authenticated session")

        if len(transactions) > MAX_BATCH_SIZE:
            raise BatchTooLargeError(f"Batch size {len(transactions)} exceeds max of {MAX_BATCH_SIZE}")

        push_to_queue(session, transactions, device_id, user_id)
        transaction_ids = [t["transaction_id"] for t in transactions]
        results = process_queue(session, transaction_ids=transaction_ids)

        for result in results:
            if result["status"] == "synced":
                _create_audit_log(session, user_id, "SYNC_COMMIT", result["transaction_id"], {"server_id": result["server_id"]})
            elif result["status"] == "conflict":
                _create_audit_log(session, user_id, "SYNC_CONFLICT", result["transaction_id"], {"message": result["message"]})

        return results

    @staticmethod
    def pull_sync(session) -> dict:
        products = session.execute(
            select(Product).where(Product.is_active == 1)
        ).scalars().all()

        deleted_product_ids = session.execute(
            select(Product.id).where(Product.is_active == 0)
        ).scalars().all()

        users = session.execute(
            select(User).where(User.is_active == 1)
        ).scalars().all()

        return {
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "sku": p.sku,
                    "category": p.category,
                    "selling_price": float(p.selling_price),
                    "cost_price": float(p.cost_price),
                    "stock_quantity": p.stock_quantity,
                }
                for p in products
            ],
            "users": [
                {"id": u.id, "name": u.name, "role": u.role}
                for u in users
            ],
            "deleted_product_ids": list(deleted_product_ids),
        }

    @staticmethod
    def resolve_conflict(session, transaction_id: str, resolution: str, resolver_id: str) -> dict:
        result = engine_resolve_conflict(session, transaction_id, resolution)
        _create_audit_log(session, resolver_id, "SYNC_RESOLVE", transaction_id, {
            "resolution": resolution,
            "outcome": result["status"],
        })
        return result
=======
    def enqueue_change(session: Session, device_id: str, transaction_id: str, entity_type: str, operation: str, payload: dict):
        existing = session.query(SyncQueue).filter_by(transaction_id=transaction_id).first()
        if existing:
            return existing, "duplicate"

        sync_entry = SyncQueue(
            transaction_id=transaction_id,
            device_id=device_id,
            entity_type=entity_type,
            operation=operation,
            payload=payload,
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
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
