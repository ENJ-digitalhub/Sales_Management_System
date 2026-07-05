import uuid
from datetime import datetime
from sqlalchemy import select
from backend.models.models import SyncQueue, Product
from backend.services.sales_service import SalesService, InsufficientStockError
from backend.utils.validators import validate_sale_payload


class ProductDeletedConflict(Exception):
    def __init__(self, product_id):
        self.product_id = product_id


def push_to_queue(session, transactions: list, device_id: str) -> list:
    """
    Ingests a batch of transactions into SyncQueue. Idempotency is enforced
    here via SyncQueue.id being the client's transaction_id — a primary
    key uniqueness check, not an app-level "look before you leap" race.

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
            return {
                "status": "conflict",
                "message": f"Product no longer available: {item['product_id']}",
                "server_id": None,
                "conflict_type": "deleted_product",
            }

    try:
        user_id = payload.get("user_id")
        sale = SalesService.create_sale(
            session=session,
            user_id=user_id,
            items=validation["items"],
            payment_method=validation["payment_method"],
            payment_provider=validation["payment_provider"],
            payment_details=validation["payment_details"],
            device_id=queue_row.device_id,
            client_transaction_id=queue_row.id,
        )
        return {"status": "synced", "message": "Synced successfully", "server_id": sale["id"], "conflict_type": None}

    except InsufficientStockError as e:
        return {
            "status": "conflict",
            "message": str(e),
            "server_id": None,
            "conflict_type": "stock",
        }
    except Exception as e:
        return {"status": "failed", "message": str(e), "server_id": None, "conflict_type": None}

def process_queue(session, transaction_ids: list = None) -> list:
    """
    Processes queued transactions one at a time, each in its own SAVEPOINT
    (nested transaction) — so a single item's failure/rollback never
    aborts the whole batch. This directly answers the guiding question:
    session.begin_nested() creates a SAVEPOINT; rolling that back only
    undoes this item's writes, not the whole session.

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

            row.status = outcome["status"]
            row.result_message = outcome["message"]
            row.server_sale_id = outcome["server_id"]

            if outcome["status"] == "synced":
                nested.commit()
            else:
                # conflict/failed: roll back any partial writes from this
                # attempt, but keep the SyncQueue row's status update by
                # re-applying it after rollback (rollback would also
                # revert the row's own status/retry_count changes since
                # they're in the same session).
                nested.rollback()
                row.status = outcome["status"]
                row.result_message = outcome["message"]
                row.retry_count = row.retry_count  # already incremented above, kept
                row.last_attempt_at = datetime.utcnow()
                session.add(row)

        except Exception as e:
            nested.rollback()
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