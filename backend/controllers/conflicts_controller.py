from flask import request, jsonify, g
from backend.database import get_db
from backend.services.conflicts_service import ConflictsService

class ConflictsController:
    @staticmethod
    def get_conflicts():
        session = get_db()
        try:
            conflicts = ConflictsService.get_all_conflicts(session)
            return jsonify({"success": True, "conflicts": [conflict.to_dict() for conflict in conflicts]}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_conflict(transaction_id):
        session = get_db()
        try:
            conflict = ConflictsService.get_conflict(transaction_id, session)
            if not conflict:
                return jsonify({"success": False, "message": "Conflict not found"}), 404
            return jsonify({"success": True, "conflict": conflict.to_dict()}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def resolve_conflict(transaction_id):
        data = request.get_json() or {}
        resolution = data.get("resolution")
        note = data.get("note")

        if resolution not in ["approve", "reject"]:
            return jsonify({"success": False, "message": "Resolution must be either 'approve' or 'reject'"}), 400

        session = get_db()
        try:
            conflict, error = ConflictsService.resolve_conflict(session, transaction_id, resolution, g.user.id, note)
            if error:
                session.rollback()
                return jsonify({"success": False, "message": error}), 400
            session.commit()
            return jsonify({"success": True, "message": "Conflict resolved", "conflict": conflict.to_dict()}), 200
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500
