<<<<<<< HEAD
import traceback
from datetime import datetime
from flask import request, jsonify
from backend.database import get_db
from backend.services.sync_service import SyncService, BatchTooLargeError, DeviceMismatchError


class SyncController:
    def push_sync(self, current_user):
        data = request.get_json(silent=True) or {}
        device_id = data.get("device_id")
        transactions = data.get("transactions")

        if not device_id or not isinstance(transactions, list):
            return jsonify({"success": False, "message": "device_id and transactions are required"}), 400

        session = get_db()
        try:
            results = SyncService.push_sync(
                session=session,
                device_id=device_id,
                jwt_device_id=current_user.get("device_id"),
                transactions=transactions,
                user_id=current_user.get("id"),
            )
            session.commit()
            return jsonify({"success": True, "results": results}), 200

        except DeviceMismatchError as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 403

        except BatchTooLargeError as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 400

        except Exception as e:
            session.rollback()
            traceback.print_exc()  # <-- full stack trace now prints to your terminal
            return jsonify({"success": False, "message": "Sync failed", "detail": str(e)}), 500

    def pull_sync(self):
        session = get_db()
        try:
            data = SyncService.pull_sync(session)
            return jsonify({
                "success": True,
                "data": data,
                "server_timestamp": datetime.utcnow().isoformat(),
            }), 200
        except Exception as e:
            traceback.print_exc()
            return jsonify({"success": False, "message": "Pull failed", "detail": str(e)}), 500

    def resolve_conflict(self, current_user):
        data = request.get_json(silent=True) or {}
        transaction_id = data.get("transaction_id")
        resolution = data.get("resolution")

        if not transaction_id or resolution not in ("approve", "reject"):
            return jsonify({"success": False, "message": "transaction_id and valid resolution are required"}), 400

        session = get_db()
        try:
            result = SyncService.resolve_conflict(session, transaction_id, resolution, current_user["id"])
            session.commit()
            return jsonify({"success": True, "result": result}), 200
        except ValueError as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 400
        except Exception as e:
            session.rollback()
            traceback.print_exc()
            return jsonify({"success": False, "message": "Resolve failed", "detail": str(e)}), 500
=======

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
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
