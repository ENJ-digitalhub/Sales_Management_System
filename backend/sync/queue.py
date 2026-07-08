import json
from datetime import datetime, timezone

import backend.database as database
from backend.services.sync_service import SyncService
from backend.services.sales_service import SalesService
from backend.models.models import SyncQueue, AuditLog


class Queue:
    def push_to_queue(self, device_id, transaction_id, entity_type, operation, payload):
        """Enqueue a sync action using the client-supplied transaction_id for idempotency."""
        session = database.SessionLocal()
        try:
            sync_entry, error = SyncService.enqueue_change(
                session=session,
                device_id=device_id,
                transaction_id=transaction_id,
                entity_type=entity_type,
                operation=operation,
                payload=payload,
            )
            if error and error != "duplicate":
                session.rollback()
                return None, error
            session.commit()
            return sync_entry, error
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_conflicts(self, session):
        return session.query(SyncQueue).filter_by(status="conflict").all()

    def get_conflict(self, transaction_id, session):
        return session.query(SyncQueue).filter_by(transaction_id=transaction_id).first()

    def resolve_conflict(self, transaction_id, resolution, user_id, note, session):
        sync_item = session.query(SyncQueue).filter_by(transaction_id=transaction_id).first()
        if not sync_item:
            return None, "Sync item not found"

        if sync_item.status != "conflict":
            return None, "Conflict has already been resolved or is not in a resolvable state"

        if resolution not in ["approve", "reject"]:
            return None, "Invalid resolution. Must be 'approve' or 'reject'"

        payload = sync_item.payload
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                return None, "Invalid payload stored for sync item"

        sync_item.resolution = resolution
        sync_item.resolution_note = note or None
        sync_item.resolved_by = user_id
        sync_item.resolved_at = datetime.now(timezone.utc)

        if resolution == "approve":
            if sync_item.entity_type != "sale":
                return None, "Approve is only supported for sale conflicts at this time"

            items = payload.get("items")
            payment_method = payload.get("payment_method")
            if not items or not payment_method:
                return None, "Sync payload is missing sale data"

            sale, error = SalesService.create_sale(session, user_id, items, payment_method, commit=False)
            if error:
                return None, error

            sync_item.status = "synced"
            session.add(sync_item)
            session.add(AuditLog(
                user_id=user_id,
                action_type="sync_conflict",
                entity_type="sale",
                entity_id=sync_item.transaction_id,
                log_metadata={
                    "resolution": resolution,
                    "note": note,
                    "conflict_type": sync_item.conflict_type,
                    "payload": payload,
                },
                created_at=datetime.now(timezone.utc)
            ))
            return sync_item, None

        sync_item.status = "failed"
        session.add(sync_item)
        session.add(AuditLog(
            user_id=user_id,
            action_type="sync_conflict",
            entity_type=sync_item.entity_type,
            entity_id=sync_item.transaction_id,
            log_metadata={
                "resolution": resolution,
                "note": note,
                "conflict_type": sync_item.conflict_type,
                "payload": payload,
            },
            created_at=datetime.now(timezone.utc)
        ))
        return sync_item, None

    def process_queue(self, device_id=None):
        """Process pending sync queue items. If device_id is provided, process only that device's queue."""
        session = database.SessionLocal()
        try:
            if device_id:
                return SyncService.process_sync_queue(session=session, device_id=device_id)

            pending_devices = (
                session.query(SyncQueue.device_id)
                .filter_by(status="pending")
                .distinct()
                .all()
            )
            results = []
            for (device_id,) in pending_devices:
                results.extend(SyncService.process_sync_queue(session=session, device_id=device_id))
            return results
        finally:
            session.close()
