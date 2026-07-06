
from flask import request, jsonify, g
from backend.services.sync_service import SyncService
from backend.database import SessionLocal
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

        session = SessionLocal()
        try:
            results = []
            for change in changes:
                entity_type = change.get("entity_type")
                operation = change.get("operation")
                payload = change.get("payload")
                if not all([entity_type, operation, payload]):
                    results.append({"status": "failed", "message": "Invalid change format"})
                    continue
                
                sync_entry = SyncService.enqueue_change(session, g.device_id, entity_type, operation, payload)
                results.append({"status": "enqueued", "transaction_id": sync_entry.transaction_id})
            session.commit()
            return jsonify({"success": True, "results": results}), 200
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500
        finally:
            session.close()

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

        session = SessionLocal()
        try:
            changes = SyncService.get_unsynced_changes(session, last_sync_time)
            return jsonify({"success": True, "changes": changes}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
        finally:
            session.close()

    @staticmethod
    @require_auth
    def resolve_conflict():
        data = request.get_json()
        transaction_id = data.get("transaction_id")
        resolution_payload = data.get("resolution_payload")

        if not all([transaction_id, resolution_payload]):
            return jsonify({"success": False, "message": "Transaction ID and resolution payload are required"}), 400

        session = SessionLocal()
        try:
            sync_item, error = SyncService.resolve_conflict(session, transaction_id, resolution_payload)
            if error:
                session.rollback()
                return jsonify({"success": False, "message": error}), 400
            session.commit()
            return jsonify({"success": True, "message": "Conflict resolved", "sync_item": sync_item.to_dict()}), 200
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500
        finally:
            session.close()

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
