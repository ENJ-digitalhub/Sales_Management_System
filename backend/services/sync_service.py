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


class SyncService:
    @staticmethod
    def push_sync(session, device_id: str, jwt_device_id: str, transactions: list, user_id: str) -> list:
        if device_id != jwt_device_id:
            raise DeviceMismatchError("device_id does not match authenticated session")

        if len(transactions) > MAX_BATCH_SIZE:
            raise BatchTooLargeError(f"Batch size {len(transactions)} exceeds max of {MAX_BATCH_SIZE}")

        push_to_queue(session, transactions, device_id)
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