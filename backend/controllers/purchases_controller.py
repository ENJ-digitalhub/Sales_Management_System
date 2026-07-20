from flask import request, jsonify, g
from backend.services.purchases_service import PurchasesService
from backend.database import get_db
from backend.utils.auth_middleware import require_auth, require_role

class PurchasesController:
    @staticmethod
    def create_purchase():
        data = request.get_json() or {}
        items = data.get("items")
        supplier = data.get("supplier")

        if not items or not isinstance(items, list):
            return jsonify({"success": False, "message": "Items must be a non-empty list"}), 400

        session = get_db()
        try:
            purchase, error = PurchasesService.create_purchase(session, g.user.id, supplier, items)
            if error:
                session.rollback()
                return jsonify({"success": False, "message": error}), 400
            session.commit()
            return jsonify({"success": True, "purchase": purchase.to_dict()}), 201
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_purchase(purchase_id):
        session = get_db()
        try:
            purchase, error = PurchasesService.get_purchase(session, purchase_id)
            if error:
                return jsonify({"success": False, "message": error}), 404
            return jsonify({"success": True, "purchase": purchase.to_dict()}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_purchase_history():
        session = get_db()
        try:
            purchases, error = PurchasesService.get_purchase_history(session)
            if error:
                return jsonify({"success": False, "message": error}), 400
            return jsonify({"success": True, "purchases": [p.to_dict() for p in purchases]}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    @require_role("admin")
    def approve_purchase(purchase_id):
        session = get_db()
        try:
            purchase, error = PurchasesService.approve_purchase(session, purchase_id, g.user.id)
            if error:
                session.rollback()
                return jsonify({"success": False, "message": error}), 400
            session.commit()
            return jsonify({"success": True, "purchase": purchase.to_dict()}), 200
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500
