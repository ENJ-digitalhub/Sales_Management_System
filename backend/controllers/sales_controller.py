from flask import request, jsonify, g
from backend.database import get_db
from backend.services.sales_service import SalesService, InsufficientStockError
from backend.utils.validators import validate_sale_payload, validate_pagination_params


class SalesController:
    def create_sale(self, data, current_user):
        validation = validate_sale_payload(data or {}, require_transaction_id=True)
        if not validation["valid"]:
            return jsonify({"success": False, "message": validation["error"]}), 400

        session = get_db()
        try:
            result = SalesService.create_sale(
                session=session,
                user_id=current_user["id"],
                items=validation["items"],
                payment_method=validation["payment_method"],
                payment_provider=validation["payment_provider"],
                payment_details=validation["payment_details"],
                device_id=validation["device_id"],
                client_transaction_id=validation["client_transaction_id"],
            )
            session.commit()
            return jsonify({"success": True, "sale": result}), 201

        except InsufficientStockError as e:
            session.rollback()
            return jsonify({
                "success": False,
                "message": str(e),
                "product_id": e.product_id,
            }), 422

        except ValueError as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 400

        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": "Failed to create sale", "detail": str(e)}), 500

    def get_sale(self, sale_id, current_user):
        session = get_db()
        try:
            result = SalesService.get_sale(session=session, sale_id=sale_id)
            if not result:
                return jsonify({"success": False, "message": "Sale not found"}), 404
            return jsonify({"success": True, "sale": result}), 200
        except Exception as e:
            return jsonify({"success": False, "message": "Failed to fetch sale", "detail": str(e)}), 500

    def edit_sale(self, sale_id, data, current_user):
        validation = validate_sale_payload(data or {}, require_transaction_id=False)
        if not validation["valid"]:
            return jsonify({"success": False, "message": validation["error"]}), 400

        session = get_db()
        try:
            result = SalesService.edit_sale(
                session=session,
                sale_id=sale_id,
                user_id=current_user["id"],
                role=current_user["role"],
                items=validation["items"],
                payment_method=validation["payment_method"],
                payment_provider=validation["payment_provider"],
                payment_details=validation["payment_details"],
            )
            session.commit()
            return jsonify({"success": True, "sale": result}), 200

        except PermissionError as e:
            if str(e) == "edit_window_closed":
                return jsonify({
                    "success": False,
                    "message": "Edit window has closed. Manager approval required.",
                    "requires_approval": True,
                }), 403
            return jsonify({"success": False, "message": "Permission denied"}), 403

        except InsufficientStockError as e:
            session.rollback()
            return jsonify({
                "success": False,
                "message": str(e),
                "product_id": e.product_id,
            }), 422

        except ValueError as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 400

        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": "Failed to edit sale", "detail": str(e)}), 500

    def cancel_sale(self, sale_id, current_user):
        session = get_db()
        try:
            result = SalesService.cancel_sale(
                session=session,
                sale_id=sale_id,
                user_id=current_user["id"],
                role=current_user["role"],
            )
            session.commit()
            return jsonify({"success": True, "sale": result}), 200

        except ValueError as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 400

        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": "Failed to cancel sale", "detail": str(e)}), 500

    def get_products(self):
        page_param = request.args.get("page")
        per_page_param = request.args.get("per_page")
        validation = validate_pagination_params(page_param, per_page_param)
        if validation["error"]:
            return jsonify({"error": validation["error"]}), 400

        session = get_db()
        try:
            result = SalesService.get_paginated_products(
                session=session,
                page=validation["page"],
                per_page=validation["per_page"],
            )
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"error": "Failed to fetch products", "detail": str(e)}), 500

    def update_product(self, product_id):
        updates = request.get_json() or {}
        if not updates:
            return jsonify({"error": "No fields provided to update"}), 400

        session = get_db()
        try:
            result = SalesService.update_product(session, product_id, updates)
            if result is None:
                return jsonify({"error": "Product not found"}), 404
            session.commit()
            return jsonify(result), 200
        except ValueError as e:
            session.rollback()
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            session.rollback()
            return jsonify({"error": "Failed to update product", "detail": str(e)}), 500