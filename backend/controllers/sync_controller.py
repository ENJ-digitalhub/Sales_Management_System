
from flask import request, jsonify, g
from backend.services.sync_service import SyncService
from backend.services.conflicts_service import ConflictsService
from backend.database import get_db
from backend.utils.auth_middleware import require_auth
from datetime import datetime
import json
from backend.models.models import SyncQueue

class SyncController:
    @staticmethod
    @require_auth
    def push_changes():
        data = request.get_json()
        changes = data.get("changes") # List of {entity_type, operation, payload}

        if not changes:
            return jsonify({"success": False, "message": "No changes provided"}), 400

        session = get_db()
        try:
            results = []
            for change in changes:
                entity_type = change.get("entity_type")
                operation = change.get("operation")
                payload = change.get("payload")
                transaction_id = change.get("transaction_id")
                if not all([entity_type, operation, payload, transaction_id]):
                    results.append({"status": "failed", "message": "Invalid change format"})
                    continue

                sync_entry, error = SyncService.enqueue_change(session, g.device_id, transaction_id, entity_type, operation, payload)
                if error == "duplicate":
                    results.append({"status": "synced", "transaction_id": sync_entry.transaction_id})
                elif error:
                    results.append({"status": "failed", "message": error, "transaction_id": transaction_id})
                else:
                    results.append({"status": "enqueued", "transaction_id": sync_entry.transaction_id})
            session.commit()
            return jsonify({"success": True, "results": results}), 200
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    @require_auth
    def pull_changes():
        last_sync_time_str = request.args.get("last_sync_time")
        if not last_sync_time_str:
            return jsonify({"success": False, "message": "last_sync_time is required"}), 400

        try:
            last_sync_time = datetime.fromisoformat(last_sync_time_str.replace("Z", "+00:00"))
        except ValueError:
            return jsonify({"success": False, "message": "Invalid last_sync_time format"}), 400

        session = get_db()
        try:
            changes = SyncService.get_unsynced_changes(session, last_sync_time)
            return jsonify({"success": True, "changes": changes}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    @require_auth
    def resolve_conflict():
        data = request.get_json() or {}
        transaction_id = data.get("transaction_id")
        resolution = data.get("resolution")
        note = data.get("note")

        if not transaction_id or resolution not in ["approve", "reject"]:
            return jsonify({"success": False, "message": "Transaction ID and valid resolution are required"}), 400

        session = get_db()
        try:
            sync_item, error = ConflictsService.resolve_conflict(session, transaction_id, resolution, g.user.id, note)
            if error:
                session.rollback()
                return jsonify({"success": False, "message": error}), 400
            session.commit()
            return jsonify({"success": True, "message": "Conflict resolved", "sync_item": sync_item.to_dict()}), 200
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

# Helper for SyncQueue to_dict
def to_dict(self):
    return {
        "id": self.id,
        "transaction_id": self.transaction_id,
        "device_id": self.device_id,
        "entity_type": self.entity_type,
        "operation": self.operation,
        "payload": json.loads(self.payload) if isinstance(self.payload, str) else self.payload,
        "status": self.status,
        "retry_count": self.retry_count,
        "last_attempt_at": self.last_attempt_at.isoformat() if self.last_attempt_at else None,
        "created_at": self.created_at.isoformat()
    }
SyncQueue.to_dict = to_dict
