
from flask import request, jsonify, g
from backend.services.sales_service import SalesService
from backend.database import get_db
from backend.utils.auth_middleware import require_auth, require_role
from backend.models.models import Sale

class SalesController:
    @staticmethod
    @require_auth
    def create_sale():
        data = request.get_json()
        items = data.get("items")
        payment_method = data.get("payment_method")

        if not items or not payment_method:
            return jsonify({"success": False, "message": "Items and payment method are required"}), 400

        session = get_db()
        try:
            sale, error = SalesService.create_sale(session, g.user.id, items, payment_method)
            if error:
                session.rollback()
                return jsonify({"success": False, "message": error}), 400
            session.commit()
            return jsonify({"success": True, "sale": sale.to_dict()}), 201
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    @require_auth
    def get_all_sales():
        session = get_db()
        try:
            sales, error = SalesService.get_all_sales(session, user_id=g.user.id, role=g.user.role)
            if error:
                return jsonify({"success": False, "message": error}), 400
            return jsonify({"success": True, "sales": [s.to_dict() for s in sales]}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    @require_auth
    def get_sale(sale_id):
        session = get_db()
        try:
            sale, error = SalesService.get_sale(session, sale_id)
            if error:
                return jsonify({"success": False, "message": error}), 404
            return jsonify({"success": True, "sale": sale.to_dict()}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    @require_auth
    def edit_sale(sale_id):
        data = request.get_json()
        items = data.get("items")
        payment_method = data.get("payment_method")

        if not items or not payment_method:
            return jsonify({"success": False, "message": "Items and payment method are required"}), 400

        session = get_db()
        try:
            sale, error = SalesService.edit_sale(session, sale_id, g.user.id, g.user.role, items, payment_method)
            if error:
                session.rollback()
                if "Edit window has closed" in error:
                    return jsonify({"success": False, "message": error, "requires_approval": True}), 403
                return jsonify({"success": False, "message": error}), 400
            session.commit()
            return jsonify({"success": True, "sale": sale.to_dict()}), 200
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    @require_auth
    @require_role("admin", "manager")
    def cancel_sale(sale_id):
        session = get_db()
        try:
            sale, error = SalesService.cancel_sale(session, sale_id, g.user.id, g.user.role)
            if error:
                session.rollback()
                return jsonify({"success": False, "message": error}), 400
            session.commit()
            return jsonify({"success": True, "sale": sale.to_dict()}), 200
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    @require_auth
    @require_role("admin")
    def delete_sale(sale_id):
        session = get_db()
        try:
            _, error = SalesService.delete_sale(session, sale_id, g.user.id)
            if error:
                session.rollback()
                return jsonify({"success": False, "message": error}), 400
            session.commit()
            return jsonify({"success": True, "message": "Sale deleted successfully"}), 200
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    @require_auth
    def request_edit(sale_id):
        data = request.get_json() or {}
        reason = data.get("reason")
        proposed_changes = data.get("proposed_changes")

        if not reason or not isinstance(proposed_changes, dict):
            return jsonify({"success": False, "message": "Reason and proposed_changes are required"}), 400

        session = get_db()
        try:
            sale, error = SalesService.request_edit(session, sale_id, g.user.id, g.user.role, reason, proposed_changes)
            if error:
                session.rollback()
                return jsonify({"success": False, "message": error}), 400
            session.commit()
            return jsonify({"success": True, "sale": sale.to_dict(), "message": "Edit request submitted"}), 200
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500