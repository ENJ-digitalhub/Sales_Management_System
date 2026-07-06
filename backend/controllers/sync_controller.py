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