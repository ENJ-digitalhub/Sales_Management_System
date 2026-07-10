<<<<<<< HEAD
import uuid
from datetime import datetime
from sqlalchemy import select
from backend.models.models import SyncQueue, Product
from backend.services.sales_service import SalesService, InsufficientStockError
from backend.utils.validators import validate_sale_payload


class ProductDeletedConflict(Exception):
    def __init__(self, product_id):
        self.product_id = product_id


def push_to_queue(session, transactions: list, device_id: str, user_id: str) -> list:
    """
    Ingests a batch of transactions into SyncQueue. Idempotency is enforced
    here via SyncQueue.id being the client's transaction_id — a primary
    key uniqueness check, not an app-level "look before you leap" race.

    user_id is the authenticated user who is submitting this batch. It's
    stored on the row (submitted_by) at ingestion time so that later, when
    a manager resolves a conflict via resolve_conflict(), the sale can
    still be correctly attributed to the ORIGINAL submitter — not the
    resolver.

    Returns the list of transaction_ids that are actually new/pending
    (already-synced ones are skipped here, handled directly in process_queue
    when it re-encounters them).
    """
    new_ids = []
    for txn in transactions:
        transaction_id = txn["transaction_id"]
        existing = session.get(SyncQueue, transaction_id)

        if existing is not None:
            # Already known — don't touch it here. process_queue() will
            # short-circuit on this id and return its existing status.
            new_ids.append(transaction_id)
            continue

        queue_row = SyncQueue(
            id=transaction_id,
            device_id=device_id,
            submitted_by=user_id,
            entity_type=txn.get("entity_type", "sale"),
            operation=txn.get("operation", "CREATE"),
            payload=txn.get("payload", {}),
            status="pending",
            retry_count=0,
            created_at=datetime.utcnow(),
        )
        session.add(queue_row)
        new_ids.append(transaction_id)

    session.flush()
    return new_ids


def validate_transaction(session, queue_row: SyncQueue) -> dict:
    if queue_row.entity_type != "sale" or queue_row.operation != "CREATE":
        return {"status": "failed", "message": f"Unsupported entity_type/operation: {queue_row.entity_type}/{queue_row.operation}", "server_id": None, "conflict_type": None}

    payload = queue_row.payload
    validation = validate_sale_payload(payload, require_transaction_id=False)
    if not validation["valid"]:
        return {"status": "failed", "message": validation["error"], "server_id": None, "conflict_type": None}

    for item in validation["items"]:
        product = session.get(Product, item["product_id"])
        if product is None or product.is_active == 0:
            return {"status": "conflict", "message": f"Product no longer available: {item['product_id']}", "server_id": None, "conflict_type": "deleted_product"}

    try:
        # user_id comes from the row itself (set at ingestion in
        # push_to_queue), NOT from the payload — the locked POST /sync
        # contract's payload only contains items/payment_method, so
        # payload.get("user_id") was always None. Reading it from
        # queue_row.submitted_by also means resolve_conflict() later
        # attributes the sale correctly to the original submitter,
        # even if a different user (e.g. a manager) resolves it.
        user_id = queue_row.submitted_by
        sale = SalesService.create_sale(
            session=session,
            user_id=user_id,
            items=validation["items"],
            payment_method=validation["payment_method"],
            device_id=queue_row.device_id,
            client_transaction_id=queue_row.id,
        )
        return {"status": "synced", "message": "Synced successfully", "server_id": sale["id"], "conflict_type": None}

    except InsufficientStockError as e:
        return {"status": "conflict", "message": str(e), "server_id": None, "conflict_type": "stock"}
    except Exception as e:
        return {"status": "failed", "message": str(e), "server_id": None, "conflict_type": None}


def _safe_rollback(nested):
    """
    Rolls back a SAVEPOINT defensively.

    WHY THIS EXISTS (please read before removing):
    When a flush inside validate_transaction() (e.g. inside
    SalesService.create_sale()) hits a DB-level error such as
    InsufficientStockError, SQLAlchemy can auto-deactivate the current
    SAVEPOINT as part of surfacing that error — even though we catch
    the error cleanly inside validate_transaction() and return a normal
    "conflict"/"failed" dict instead of raising.

    That means by the time process_queue() calls nested.rollback()
    explicitly, the savepoint may already be closed. Calling .rollback()
    on an already-closed savepoint raises sqlalchemy.exc.ResourceClosedError
    ("This transaction is closed"), which then masks the real outcome and
    crashes the whole /sync request with a 500 — even though the actual
    conflict/failure was already handled correctly.

    This helper checks nested.is_active first, and swallows
    ResourceClosedError as a fallback, so a savepoint that already closed
    itself is simply treated as "already rolled back" instead of raising.
    """
    try:
        if nested.is_active:
            nested.rollback()
    except Exception:
        # Already closed/invalidated — nothing more to do.
        pass


def process_queue(session, transaction_ids: list = None) -> list:
    """
    Processes queued transactions one at a time, each in its own SAVEPOINT
    (nested transaction) — so a single item's failure/rollback never
    aborts the whole batch. session.begin_nested() creates a SAVEPOINT;
    rolling that back only undoes this item's writes, not the whole session.

    Idempotency: if a row's status is already 'synced', we skip real
    work and return its cached result immediately — no second DB write,
    no second stock decrement.
    """
    query = select(SyncQueue)
    if transaction_ids:
        query = query.where(SyncQueue.id.in_(transaction_ids))
    else:
        query = query.where(SyncQueue.status == "pending")

    rows = session.execute(query).scalars().all()
    results = []

    for row in rows:
        if row.status == "synced":
            results.append({
                "transaction_id": row.id,
                "status": "synced",
                "message": row.result_message or "Already synced",
                "server_id": row.server_sale_id,
            })
            continue

        row.retry_count += 1
        row.last_attempt_at = datetime.utcnow()

        # SAVEPOINT — this item's failure rolls back only this item.
        nested = session.begin_nested()
        try:
            outcome = validate_transaction(session, row)

            if outcome["status"] == "synced":
                row.status = outcome["status"]
                row.result_message = outcome["message"]
                row.server_sale_id = outcome["server_id"]
                nested.commit()
            else:
                # conflict/failed: roll back any partial writes from this
                # attempt (defensively — see _safe_rollback docstring),
                # then re-apply the row's own status/message so the
                # SyncQueue record still reflects the outcome even though
                # the underlying sale attempt was undone.
                _safe_rollback(nested)
                row.status = outcome["status"]
                row.result_message = outcome["message"]
                row.server_sale_id = outcome["server_id"]
                session.add(row)

        except Exception as e:
            _safe_rollback(nested)
            row.status = "failed"
            row.result_message = str(e)
            session.add(row)

        session.flush()

        results.append({
            "transaction_id": row.id,
            "status": row.status,
            "message": row.result_message,
            "server_id": row.server_sale_id,
        })

    return results


def resolve_conflict(session, transaction_id: str, resolution: str) -> dict:
    """
    resolution == 'approve': re-attempts the transaction now (stock may
    have changed since the original conflict — e.g. a restock happened).
    resolution == 'reject': marks it failed permanently, no further retries.
    """
    row = session.get(SyncQueue, transaction_id)
    if row is None:
        raise ValueError("Transaction not found")

    if row.status != "conflict":
        raise ValueError(f"Transaction is not in conflict state (current: {row.status})")

    if resolution == "reject":
        row.status = "failed"
        row.result_message = "Rejected by manager"
        session.flush()
        return {"transaction_id": row.id, "status": "failed", "message": row.result_message}

    if resolution == "approve":
        outcome = validate_transaction(session, row)
        row.status = outcome["status"]
        row.result_message = outcome["message"]
        row.server_sale_id = outcome["server_id"]
        row.last_attempt_at = datetime.utcnow()
        session.flush()
        return {"transaction_id": row.id, "status": row.status, "message": row.result_message}

    raise ValueError("resolution must be 'approve' or 'reject'")
=======
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
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
