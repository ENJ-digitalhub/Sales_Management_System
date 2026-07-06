# backend/controllers/sales_controller.py
from flask import request, jsonify, g
from backend.database import get_db
from backend.services.sales_service import SalesService, InsufficientStockError
from backend.utils.validators import validate_sale_payload


class SalesController:

    def create_sale(self):
        data = request.get_json() or {}
        validation = validate_sale_payload(data)
        if not validation["valid"]:
            return jsonify({"success": False, "message": validation["error"]}), 400

        session = get_db()
        try:
            result = SalesService.create_sale(
                session=session,
                user_id=g.current_user["id"],
                items=validation["items"],
                payment_method=validation["payment_method"],
            )
            session.commit()
            return jsonify({"success": True, "sale": result}), 201

        except InsufficientStockError as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e), "product_id": e.product_id}), 422
        except ValueError as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 400

    def get_sale(self, sale_id):
        session = get_db()
        result = SalesService.get_sale(session, sale_id)
        if not result:
            return jsonify({"success": False, "message": "Sale not found"}), 404
        return jsonify({"success": True, "sale": result}), 200

    def edit_sale(self, sale_id):
        data = request.get_json() or {}
        validation = validate_sale_payload(data)
        if not validation["valid"]:
            return jsonify({"success": False, "message": validation["error"]}), 400

        session = get_db()
        try:
            result = SalesService.edit_sale(
                session=session,
                sale_id=sale_id,
                user_id=g.current_user["id"],
                role=g.current_user["role"],
                items=validation["items"],
                payment_method=validation["payment_method"],
            )
            session.commit()
            return jsonify({"success": True, "sale": result}), 200

        except PermissionError:
            return jsonify({
                "success": False,
                "message": "Edit window has closed. Manager approval required.",
                "requires_approval": True,
            }), 403
        except InsufficientStockError as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e), "product_id": e.product_id}), 422
        except ValueError as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 400

    def cancel_sale(self, sale_id):
        session = get_db()
        try:
            result = SalesService.cancel_sale(
                session=session,
                sale_id=sale_id,
                user_id=g.current_user["id"],
                role=g.current_user["role"],
            )
            session.commit()
            return jsonify({"success": True, "sale": result}), 200
        except ValueError as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 400